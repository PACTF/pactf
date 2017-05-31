"""Define views to override CTFlex"""

import logging
from functools import partial

from django.core.cache import cache
from django.http import Http404
from django.shortcuts import render
from django.views.decorators.cache import never_cache

from ctflex import queries
from ctflex.settings import OVERALL_WINDOW_CODENAME, SCORE_NORMALIZATION, BOARD_CACHE_DURATION
from ctflex.constants import BASE_LOGGER_NAME, BOARD_CACHE_KEY_PREFIX
from ctflex.queries import _team_ranking_key
from ctflex.views import limited_http_methods, defaulted_window, windowed_context
from ctflex import models
from pactf_web.constants import TIEBREAKER_WINDOW_CODENAME

logger = logging.getLogger(BASE_LOGGER_NAME + '.' + __name__)

_TIEBREAKER_SCORES = {
    'Th3g3ntl3man': 3103,  # 3102699.34844,
    'phsst': 886,  # 886421.793368,
    'Flaming Tigers': 880,  # 880482.761238,
    'b1c': 864,  # 864275.412813,
    'REEEEEEEEEEEEEEEEEEEEEEEEEEEEE': 861,  # 861110.999622,
    'sos brigade': 820,  # 819581.007839,
    'Opensource Potato': 791,  # 791515.895325,
    'MemeDream': 394,  # 393643.230587,
    'unlimited reagents': 344,  # 343889.0261,
    'BS and the Big Boys': 307,  # 306502.026282,
    'SFHS Team C': 37,  # 36971.5204705,
    'GO GO MUSTANGS': 4,  # 4121.27172823
    'AT-Fun': 928,  # 927829
}

_TIEBREAKER_MAX = 4000  # arbitrary


def _teams_with_score_tiebreaker():

    board = cache.get(BOARD_CACHE_KEY_PREFIX + TIEBREAKER_WINDOW_CODENAME)
    if board:
        logger.debug("using cache for board tiebreaker")
        return board

    teams_with_score = (
        (team, _TIEBREAKER_SCORES[team.name])
        for i, team in enumerate(models.Team.objects
                                 .exclude(standing=models.Team.INVISIBLE_STANDING)
                                 .iterator())
        if team.name in _TIEBREAKER_SCORES
    )
    ranked = sorted(teams_with_score, key=partial(_team_ranking_key, None))
    board = tuple((i + 1, team, score_) for i, (team, score_) in enumerate(ranked))

    logger.debug("computing board for tiebreaker")
    cache.set(BOARD_CACHE_KEY_PREFIX + TIEBREAKER_WINDOW_CODENAME, board, BOARD_CACHE_DURATION)
    return board


def _teams_with_score_overall_tiebreaker():

    board = cache.get(BOARD_CACHE_KEY_PREFIX + OVERALL_WINDOW_CODENAME + TIEBREAKER_WINDOW_CODENAME)
    if board:
        logger.debug("using cache for board overall tiebreaker")
        return board

    teams_with_score = (
        (team, score + int(
            SCORE_NORMALIZATION * _TIEBREAKER_SCORES.get(team.name, 0) / _TIEBREAKER_MAX
        )) for rank, team, score in queries.board_cached()
    )
    ranked = sorted(teams_with_score, key=partial(_team_ranking_key, None))
    board = tuple((i + 1, team, score_) for i, (team, score_) in enumerate(ranked))

    logger.debug("computing board for overall tiebreaker")
    cache.set(BOARD_CACHE_KEY_PREFIX + OVERALL_WINDOW_CODENAME + TIEBREAKER_WINDOW_CODENAME, board, BOARD_CACHE_DURATION)
    return board


@never_cache
@limited_http_methods('GET')
@defaulted_window()
def board(request, *, window_codename):
    """Render board post-competition incorporating tiebreaker results"""

    # Get window
    if window_codename in (OVERALL_WINDOW_CODENAME, TIEBREAKER_WINDOW_CODENAME):
        window = None
    else:
        try:
            window = queries.get_window(window_codename)
        except models.Window.DoesNotExist:
            raise Http404()

    # Initialize context
    context = windowed_context(window)
    context['overall_window_codename'] = OVERALL_WINDOW_CODENAME
    context['tiebreaker_window_codename'] = TIEBREAKER_WINDOW_CODENAME
    context['is_tiebreaker'] = window_codename == TIEBREAKER_WINDOW_CODENAME

    # Compute board
    if window_codename == OVERALL_WINDOW_CODENAME:
        context['board'] = _teams_with_score_overall_tiebreaker()
    elif window_codename == TIEBREAKER_WINDOW_CODENAME:
        context['board'] = _teams_with_score_tiebreaker()
    else:
        context['board'] = queries.board_cached(window)

    if window_codename == OVERALL_WINDOW_CODENAME:
        context['current_window'] = queries.get_window()
        context['score_normalization'] = SCORE_NORMALIZATION
        template_name = 'pactf_web/board/overall.html'
    elif window_codename == TIEBREAKER_WINDOW_CODENAME:
        template_name = 'pactf_web/board/tiebreaker.html'
    else:
        assert window.ended()
        template_name = 'pactf_web/board/ended.html'

    return render(request, template_name, context)
