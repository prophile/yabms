"""Validator: no match has the same team twice."""

from collections import Counter

from .validators import error, validator


@validator("duplicates")
def validate_dupes(schedule):
    """Validate that no match has the same team twice."""
    for ix, match in enumerate(schedule):
        appearances = Counter(match)
        duplicate_teams = [team for team, count in appearances.items() if count > 1]
        duplicate_teams.sort()
        for team in duplicate_teams:
            yield error(
                "dupe", f"Team {team} appears in match {ix} {appearances[team]} times"
            )
