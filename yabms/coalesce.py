"""
Coalesce proto-rounds.

Having built a valid proto-round, we can coalesce multiple
proto-rounds together to build a single schedule.
"""

import itertools
import random
import sys

import tqdm


def _is_valid(provisional, *, spacing=1):
    all_teams = sorted({y for x in provisional for y in x})

    # Check the spacing constraint
    zone_count = len(provisional[0])
    for window_start in range(len(provisional) - spacing):
        window = provisional[window_start : window_start + spacing + 1]
        teams = {y for x in window for y in x}
        if len(teams) != zone_count * (spacing + 1):
            return False

    # Check the max-facing constraint
    facings = {
        (x, y): 0 for n, x in enumerate(all_teams[:-1]) for y in all_teams[n + 1 :]
    }

    for match in provisional:
        for left_team, right_team in itertools.combinations(sorted(match), 2):
            facings[left_team, right_team] += 1

    highest_facing = max(facings.values())
    lowest_facing = min(facings.values())

    if highest_facing - lowest_facing > 2:
        return False

    return True


def coalesce(proto_round, num_rounds, *, spacing=1):
    """Coalesce a proto-round sequence into a schedule."""
    # For each round, we need to select a team assignment of
    # the proto-round which preserves the spacing window.
    # TODO: Implement the max-facing constraint here too.
    confirmed = proto_round

    num_teams = len({y for x in proto_round for y in x})
    teams = list(range(num_teams))

    print("Coalescing proto-rounds into full schedule...", file=sys.stderr)
    for round_number in tqdm.trange(1, num_rounds):
        # For each round, we need to select a team assignment of
        # the proto-round which preserves the spacing window.
        for _ in range(1_000_000):
            random.shuffle(teams)

            provisional = list(confirmed)  # Copy the confirmed list
            this_round = [[teams[n] for n in match] for match in proto_round]
            provisional += this_round
            if _is_valid(provisional):
                confirmed = provisional
                break
        else:
            raise ValueError("Could not find a valid schedule.")

    return confirmed
