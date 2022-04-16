"""Validator: teams face a balanced mixture of other teams."""

import itertools

from .validator_equal_appearances import validate_equal_appearances
from .validators import error, validator, warning


@validator("facing", after=[validate_equal_appearances])
def validate_facing(schedule):
    """Validate that no two matches have the same teams."""
    all_teams = sorted({team for match in schedule for team in match})

    facings = {
        (left_team, right_team): 0
        for ix, left_team in enumerate(all_teams[:-1])
        for right_team in all_teams[ix + 1 :]
    }

    for match in schedule:
        for left_team, right_team in itertools.combinations(sorted(match), 2):
            facings[left_team, right_team] += 1

    most_facings = max(facings.values())

    for (left_team, right_team), facings_between in facings.items():
        facing_unbalance = most_facings - facings_between

        if facing_unbalance <= 1:
            continue

        if facing_unbalance == 2:
            yield warning(
                "unequal-facings",
                f"Team {left_team} and {right_team} face each other {facings_between} times, ideally {most_facings}",
            )
        else:
            yield error(
                "unequal-facings",
                f"Team {left_team} and {right_team} face only {facings_between} times, ideally {most_facings}",
            )
