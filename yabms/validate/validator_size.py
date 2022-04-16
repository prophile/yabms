"""Validator: all matches have the same number of teams."""

from .validators import error, validator


@validator("size")
def validate_size(schedule):
    """Validate that all matches have the same number of teams."""
    num_teams = len(schedule[0])

    for ix, match in enumerate(schedule):
        if len(match) != num_teams:
            yield error(
                "wrong-size", f"Match {ix} has {len(match)} teams, expected {num_teams}"
            )
