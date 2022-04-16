"""Validator: teams all appear the same number of times."""

from collections import Counter

from .validators import error, validator


@validator("equal_appearances")
def validate_equal_appearances(schedule):
    """Validate that all teams appear the same number of times."""
    num_appearances = Counter(team for match in schedule for team in match)

    most_appearances = max(num_appearances.values())

    for team in sorted(num_appearances.keys()):
        if num_appearances[team] != most_appearances:
            yield error(
                "unequal-appearances",
                f"Team {team} appears {num_appearances[team]} times, expected {most_appearances}",
            )
