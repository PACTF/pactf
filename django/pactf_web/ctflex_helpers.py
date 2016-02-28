"""Define models"""

from django_countries.fields import Country

from ctflex import models


def eligible(team):
    """Determine eligibility of team

    This function is used by CTFlex.
    """
    return not team.banned and all(
        competitor.country == Country('US')
        and competitor.background == models.Competitor.HIGHSCHOOL
        for competitor in team.competitor_set.all()
    )
