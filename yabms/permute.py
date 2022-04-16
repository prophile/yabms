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

    best_possible_entropy = math.log(sum(appearance_counts.values()))

    # We want to maximise the entropy of the distribution.
    #
    # The entropy is -Σ p log(p) where p is the number of team/zone appearances
    # divided by the total number of appearances.
    #
    # Fortunately since this is a discrete and relatively small space, we can
    # just compute the naïve entropy directly.
    entropy = _entropy(appearance_counts)

    # Since we're measuring badness though, which needs to be minimised, we
    # subtract the entropy from the theoretical maximum (so that if the
    # maximum is reached, the badness is 0). In this way, the 'badness
    # score' is essentially the number of nats to go until reaching the
    # exact entropy of a uniform distribution.
    return best_possible_entropy - entropy


def permute_zones(schedule):
    """Permute the zones in a schedule for balance."""
    # Do a hard copy
    schedule = [list(x) for x in schedule]

    print("Balancing zones...", file=sys.stderr)

    num_iterations = 1_000

    for n in tqdm.trange(num_iterations):
        made_changes = False

        score = _badness(schedule)
        # print(f"Iteration {n}: {score}", file=sys.stderr)

        if score < 1e-6:
            break

        for ix, match in enumerate(schedule):
            best_permutation = min(
                itertools.permutations(match),
                key=lambda perm: _badness(
                    itertools.chain(schedule[:ix], (perm,), schedule[ix + 1 :])
                ),
            )
            if match != list(best_permutation):
                # print(
                #     f"Altered match {ix} from {match} to {best_permutation}",
                #     file=sys.stderr,
                # )
                made_changes = True
                schedule[ix] = list(best_permutation)

        if not made_changes:
            # Do an annealing step.
            temperature = (1 - n / num_iterations) ** 2
            for match in schedule:
                if random.random() < temperature:
                    random.shuffle(match)

    return schedule
