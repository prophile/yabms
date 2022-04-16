"""Permute zones."""

import collections
import itertools
import math
import random
import sys

import tqdm


def _entropy(counter):
    """Compute the entropy of a counter."""
    total_count = sum(counter.values())
    return -sum((x / total_count) * math.log(x / total_count) for x in counter.values())


def _badness(schedule):
    """Compute how bad the zone collisions in the schedule are."""
    appearance_counts = collections.Counter(
        (team, zone_number)
        for match in schedule
        for zone_number, team in enumerate(match)
    )
    if min(appearance_counts.values()) == max(appearance_counts.values()):
        return 0
    # We want to maximise the entropy of the distribution.
    #
    # The entropy is -Σ p log(p) where p is the number of team/zone appearances
    # divided by the total number of appearances.
    #
    # Fortunately since this is a discrete and relatively small space, we can
    # just compute the naïve entropy directly.
    entropy = _entropy(appearance_counts)

    # Since we're measuring badness though, which needs to be minimised, we
    # invert the entropy. Inversion is preferable to negation here since it
    # preserves the above condition of badness = 0 meaning perfect balance.
    return 1.0 / entropy


def permute_zones(schedule):
    """Permute the zones in a schedule for balance."""
    # Do a hard copy
    schedule = [list(x) for x in schedule]

    print("Balancing zones...", file=sys.stderr)

    for n in tqdm.trange(100):
        made_changes = False

        score = _badness(schedule)
        # print(f"Iteration {n}: {score}", file=sys.stderr)

        if score == 0:
            break

        for ix, match in enumerate(schedule):
            best_permutation = min(
                itertools.permutations(match),
                key=lambda perm: _badness(
                    itertools.chain(schedule[:ix], (perm,), schedule[ix + 1 :])
                ),
            )
            if match != list(best_permutation):
                # print(f"Altered match {ix} from {match} to {best_permutation}")
                made_changes = True
                schedule[ix] = list(best_permutation)

        if not made_changes:
            # Do an annealing step.
            for match in schedule:
                if random.random() < 0.05:
                    random.shuffle(match)

    return schedule
