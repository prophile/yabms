"""Permute zones."""

import sys
import random
import statistics
import collections

def permute_zones(schedule):
    """Permute the zones in a schedule for balance."""

    # Do a hard copy
    schedule = [list(x) for x in schedule]
    best_schedule = [list(x) for x in schedule]
    best_score = float('inf')

    print("Balancing zones...", file=sys.stderr)

    match_numbers = list(range(len(schedule)))

    for n in range(1_000_000):
        appearance_counts = collections.Counter(
            (team, zone_number)
            for match in schedule
            for zone_number, team in enumerate(match)
        )
        highest_count = max(appearance_counts.values())
        lowest_count = min(appearance_counts.values())
        if highest_count == lowest_count:
            # Perfectly balanced, as all things should be.
            return schedule

        score = statistics.mean(appearance_counts.values())
        if score < best_score:
            best_schedule = [list(x) for x in schedule]
            best_score = score

        # Pick a random team/zone pair at the highest count
        highest_team, highest_zone = random.choice([
            k
            for k, v in appearance_counts.items()
            if v == highest_count
        ])

        # Find a match with this team in this zone and permute it.
        random.shuffle(match_numbers)
        for match_number in match_numbers:
            if schedule[match_number][highest_zone] == highest_team:
                random.shuffle(schedule[match_number])
                break
        
        if n and n % 10_000 == 0:
            #print(f"{n} iterations, {highest_count} to {lowest_count}, score={score:.3f}", file=sys.stderr)
            pass
    
    return best_schedule