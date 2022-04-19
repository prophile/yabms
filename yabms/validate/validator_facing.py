"""Validator: teams face a balanced mixture of other teams."""

import itertools

from .validator_equal_appearances import validate_equal_appearances
from .validators import error, validator, warning

FACING_WARNING_THRESHOLD = 3
FACING_ERROR_THRESHOLD = 4


@validator("facing", after=[validate_equal_appearances])
def validate_facing(schedule):
    """Validate that teams face a balanced mixture of other teams."""
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

    example_most_facings_pair_a, example_most_facings_pair_b = next(
        facing for facing, count in facings.items() if count == most_facings
    )

    for (left_team, right_team), facings_between in facings.items():
        facing_unbalance = most_facings - facings_between

        if facing_unbalance < FACING_WARNING_THRESHOLD:
            continue

        if facing_unbalance < FACING_ERROR_THRESHOLD:
            yield warning(
                "unequal-facings",
                f"Team {left_team} and {right_team} face each other {facings_between} times, ideally {most_facings} (cf {example_most_facings_pair_a} and {example_most_facings_pair_b})",
            )
        else:
            yield error(
                "unequal-facings",
                f"Team {left_team} and {right_team} face only {facings_between} times, ideally {most_facings} (cf {example_most_facings_pair_a} and {example_most_facings_pair_b})",
            )
