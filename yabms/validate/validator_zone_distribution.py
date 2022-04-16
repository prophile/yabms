"""Validator: teams have a balanced distribution of zones."""

from collections import Counter

from .validator_size import validate_size
from .validators import error, validator, warning


@validator("zone_distribution", after=[validate_size])
def validate_zone_distribution(schedule):
    """Validate that teams have a fair distribution of zones."""
    teams = {team for match in schedule for team in match}

    num_zones = len(schedule[0])

    appearances_by_team_and_zone = Counter(
        (team, zone) for match in schedule for zone, team in enumerate(match)
    )

    for team in teams:
        zone_appearances = [
            appearances_by_team_and_zone[team, zone] for zone in range(num_zones)
        ]
        fewest_appearances_in_this_team = min(zone_appearances)
        most_appearances_in_this_team = max(zone_appearances)
        unbalance = most_appearances_in_this_team - fewest_appearances_in_this_team
        if unbalance == 0:
            continue

        try:
            witness_fewest = next(
                zone
                for zone in range(num_zones)
                if appearances_by_team_and_zone[team, zone]
                == fewest_appearances_in_this_team
            )
            witness_most = next(
                zone
                for zone in range(num_zones)
                if appearances_by_team_and_zone[team, zone]
                == most_appearances_in_this_team
            )
        except StopIteration:
            raise AssertionError("Could not witness appearances")

        if unbalance == 1:
            yield warning(
                "unbalanced-passable",
                f"Team {team} has a 1-appearance unbalance - appears {most_appearances_in_this_team} times in zone {witness_most} and {fewest_appearances_in_this_team} times in zone {witness_fewest}",
            )
        elif unbalance > 1:
            yield error(
                "unbalanced-impassable",
                f"Team {team} has a multi-appearance unbalance - appears {most_appearances_in_this_team} times in zone {witness_most} and {fewest_appearances_in_this_team} times in zone {witness_fewest}",
            )
