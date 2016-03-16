"""Define models"""


def eligible(team):
    """Determine eligibility of team

    This function is used by CTFlex.
    """
    return (not team.banned
            and team.country == team.US_COUNTRY
            and team.background == team.SCHOOL_BACKGROUND)
