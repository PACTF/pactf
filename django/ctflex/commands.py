"""Allow views to manipulate models"""

import importlib.machinery
from os.path import join

from django.conf import settings
from django.core.exceptions import ValidationError

from ctflex import hashers
from ctflex import models


# region Misc

def start_timer(*, team, window):
    if not window.started() or window.ended() or team.has_timer(window):
        return False

    timer = models.Timer(team=team, window=window)

    try:
        timer.save()

    except ValidationError as err:
        print(err.messages)
        return False

    return True


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


class FlagSubmissionNotAllowException(Exception):
    pass


class ProblemAlreadySolvedException(Exception):
    pass


class FlagAlreadyTriedException(Exception):
    pass

class EmptyFlagException(Exception):
    pass


def submit_flag(*, prob_id, competitor, flag):
    problem = models.CtfProblem.objects.get(pk=prob_id)

    # Confirm that the team can submit flags
    window = problem.window
    if not window.ended() and not competitor.team.has_active_timer(window):
        raise FlagSubmissionNotAllowException()

    # Check if the problem has already been solved
    if models.Solve.objects.filter(problem=problem, competitor__team=competitor.team).exists():
        # logger.info('submit_flag: Team ' + competitor.team.id + ' has already solved problem ' + problem.id + '.')
        raise ProblemAlreadySolvedException()

    # Grade
    correct, message = _grade(problem=problem, flag=flag, team=competitor.team)

    if correct:
        # This effectively updates the score too
        models.Solve(problem=problem, competitor=competitor, flag=flag).save()
        # logger.info('submit_flag: Team ' + competitor.team.id + ' solved problem ' + problem.id + '.')

    elif not flag:
        # logger.info("empty flag for {} and {}".format(problem, team))
        raise EmptyFlagException()

    # Inform the user if they had already tried the same flag
    # (This check must come after actually grading as a team might have submitted a flag
    # that later becomes correct on a problem's being updated. It must also come after the check for emptiness of flag.)
    elif models.Submission.objects.filter(problem_id=prob_id, competitor__team=competitor.team, flag=flag).exists():
        # logger.info('submit_flag: Team ' + competitor.team.id + ' has already tried incorrect flag "' + flag + '" for problem ' + problem.id + '.')
        raise FlagAlreadyTriedException()

    # For logging purposes, mainly
    models.Submission(p_id=problem.id, competitor=competitor, flag=flag, correct=correct).save()

    return correct, message

# endregion
