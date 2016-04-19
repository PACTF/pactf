"""Proxy manipulation of models and other actions by views"""

import importlib.machinery
from itertools import chain
from os.path import join

from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from post_office import mail

from ctflex import hashers
from ctflex import models
from ctflex import queries
from ctflex import settings


# region Email
from ctflex.constants import MAX_FLAG_SIZE


def confirm_registration(user):
    """Confirm registration with user"""

    # Don’t do anything if the email host isn’t defined
    if not settings.EMAIL_HOST:
        return

    context = {
        'user': user,
        'support_email': settings.SUPPORT_EMAIL,
        'sitename': settings.SITENAME,
    }

    message = render_to_string('ctflex/email/registration.txt', context)
    subject = render_to_string('ctflex/email/registration.subject.txt', context)

    mail.send(
        user.email,
        settings.DEFAULT_FROM_EMAIL,

        subject=subject,
        message=message,
    )


# endregion


# region Misc

def start_timer(*, team, window):
    # XXX(Yatharth): Email other team members

    if not window.started() or window.ended() or team.has_timer(window):
        return False

    timer = models.Timer(team=team, window=window)

    try:
        timer.save()

    except ValidationError:
        return False

    return True


def mark_announcements_read(user):
    if queries.is_competitor(user):
        user.competitor.unread_announcements.clear()


def refresh_boards():
    for window in chain(queries.all_windows(), [None]):
        queries._board_uncached(window)


# endregion


# region Flag Submission

def _grade(*, problem, flag, team):
    # logger.debug("grading {} for {} with flag {!r}".format(problem, team, flag))
    grader_path = join(settings.PROBLEMS_DIR, problem.grader)  # XXX(Yatharth): Handle FileNotFound
    grader = importlib.machinery.SourceFileLoader('grader', grader_path).load_module()

    # XXX(Yatharth): Handle no such function or signature or anything, logging appropriate error messages
    correct, message = grader.grade(hashers.dyanamic_problem_key(team), flag)
    # logger.info('_grade: Flag by team ' + team.id + ' for problem ' + problem.id + ' is ' + correct + '.')
    return correct, message


class FlagSubmissionNotAllowedException(ValueError):
    pass


class ProblemAlreadySolvedException(ValueError):
    pass


class FlagAlreadyTriedException(ValueError):
    pass


class EmptyFlagException(ValueError):
    pass


class FlagTooLongException(ValueError):
    pass


def submit_flag(*, prob_id, competitor, flag):
    problem = models.CtfProblem.objects.get(pk=prob_id)

    # Confirm that the team can submit flags
    window = problem.window
    if (not competitor.user.is_superuser and not window.ended()
        and not competitor.team.has_active_timer(window)):
        raise FlagSubmissionNotAllowedException()

    # Check if the problem has already been solved
    if models.Solve.objects.filter(problem=problem, competitor__team=competitor.team).exists():
        raise ProblemAlreadySolvedException()

    # Validate some basic things
    if not flag:
        raise EmptyFlagException()
    elif len(flag) > MAX_FLAG_SIZE:
        raise FlagTooLongException()

    # Grade
    correct, message = _grade(problem=problem, flag=flag, team=competitor.team)

    # If correct, create solve, effectively updating the score too
    if correct:
        solve = models.Solve(problem=problem, competitor=competitor, flag=flag)
        solve.save()

    # Inform the user if they had already tried the same flag
    # (This check must come after actually grading as a team might have submitted a flag
    # that later becomes correct on a problem's being updated. It must also come after the check for emptiness of flag.)
    elif models.Submission.objects.filter(problem_id=prob_id, competitor__team=competitor.team, flag=flag).exists():
        raise FlagAlreadyTriedException()

    # Else, incorrect
    else:
        solve = None

    # Log submission
    models.Submission(p_id=problem.id, competitor=competitor, flag=flag, correct=correct).save()

    return correct, message, solve

# endregion
