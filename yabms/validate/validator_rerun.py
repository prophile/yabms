"""Validator: no two matches have the same teams."""

from .validator_dupes import validate_dupes
from .validators import error, validator


@validator("reruns", after=[validate_dupes])
def validate_reruns(schedule):
    """Validate that no two matches have the same teams."""
    combinations = {}

    for ix, match in enumerate(schedule):
        teams_this_match = frozenset(match)

        if teams_this_match in combinations:
            previous_ix = combinations[teams_this_match]
            teams_this_match_str = ", ".join(sorted(match))
            yield error(
                "rerun",
                f"Match {ix} has the same teams as match {previous_ix} ({teams_this_match_str})",
            )
        else:
            combinations[teams_this_match] = ix
