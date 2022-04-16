"""Validator: teams names are consecutive numbers."""

from .validators import validator, warning


@validator("numeric")
def validate_numeric(schedule):
    """Validate that teams names are consecutive numbers."""
    all_teams = sorted({team for match in schedule for team in match})

    numeric_teams = []

    for team in all_teams:
        try:
            numeric_teams.append(int(team))
        except ValueError:
            yield warning(
                "non-numeric",
                f"Team {team!r} is not a number",
            )

    lowest_team = min(numeric_teams)
    highest_team = max(numeric_teams)

    if lowest_team != 1:
        yield warning(
            "non-one-indexed",
            f"Team numbers are not one-indexed, lowest is {lowest_team}",
        )
    else:
        if highest_team != len(all_teams):
            yield warning(
                "non-consecutive",
                f"Team numbers are not consecutive, highest is {highest_team} but should be {len(all_teams)}",
            )
