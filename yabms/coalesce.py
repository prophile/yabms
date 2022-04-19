"""
Coalesce proto-rounds.

Having built a valid proto-round, we can coalesce multiple
proto-rounds together to build a single schedule.
"""

import itertools
import sys

import tqdm
import z3


def _possible_facings_per_match(match_size):
    # 2 zones: 1 facing
    # 3 zones: 3 facings
    # 4 zones: 6 facings
    # 5 zones: 10 facings
    return match_size * (match_size - 1) // 2


def _total_facings(match_size, num_matches):
    return _possible_facings_per_match(match_size) * num_matches


def _total_facings_per_team_pair(match_size, num_matches, num_teams):
    total_facings = _total_facings(match_size, num_matches)
    total_matchups = num_teams * (num_teams - 1) // 2
    return total_facings // total_matchups


def coalesce(proto_round, num_rounds, *, spacing=1):
    """Coalesce a proto-round sequence into a schedule."""
    print("Coalescing proto-rounds...", file=sys.stderr)

    if num_rounds == 1:
        # No additional work required
        return proto_round

    teams = sorted({y for x in proto_round for y in x})

    min_team = min(teams)
    max_team = max(teams)

    solver = z3.Solver()

    # Mapping of (real team, round number) -> pseudo team number
    team_to_pseudo_team = {
        (team_num, round_num): z3.Int(f"team_{team_num}_round_{round_num}")
        for team_num in teams
        for round_num in range(num_rounds)
    }

    # 1: Enforce range constraints
    print("  Adding range constraints... ", file=sys.stderr, end="")
    for allocation in team_to_pseudo_team.values():
        solver.add(allocation >= min_team)
        solver.add(allocation <= max_team)
    print(f"done, {len(solver.assertions())} constraints", file=sys.stderr)

    # 2: Enforce round bijection: each allocation is different in each round
    print("  Adding round bijection constraints... ", file=sys.stderr, end="")
    for round_num in range(num_rounds):
        solver.add(
            z3.Distinct(
                *[team_to_pseudo_team[team_num, round_num] for team_num in teams]
            )
        )
    print(f"done, {len(solver.assertions())} constraints", file=sys.stderr)

    # 3: Enforce different allocation in each round
    print("  Adding round disjointness constraints... ", file=sys.stderr, end="")
    for team_num in teams:
        solver.add(
            z3.Distinct(
                *[
                    team_to_pseudo_team[team_num, round_num]
                    for round_num in range(num_rounds)
                ]
            )
        )
    print(f"done, {len(solver.assertions())} constraints", file=sys.stderr)

    # 4: Enforce spacing constraints
    print("  Adding spacing constraints... ", file=sys.stderr, end="")
    for spacing_number in range(spacing):
        end_window_teams = [
            team_number
            for match in proto_round[-spacing_number - 1 :]
            for team_number in match
        ]
        start_window_teams = [
            team_number
            for match in proto_round[: spacing - spacing_number]
            for team_number in match
        ]

        for earlier_round_number in range(num_rounds - 1):
            later_round_number = earlier_round_number + 1

            for end_window_pseudo_team in end_window_teams:
                for start_window_pseudo_team in start_window_teams:
                    for team_number in teams:
                        solver.add(
                            z3.Not(
                                z3.And(
                                    team_to_pseudo_team[
                                        team_number, earlier_round_number
                                    ]
                                    == end_window_pseudo_team,
                                    team_to_pseudo_team[team_number, later_round_number]
                                    == start_window_pseudo_team,
                                )
                            )
                        )
    print(f"done, {len(solver.assertions())} constraints", file=sys.stderr)

    forbid_team_overlap = max(len(proto_round[0]) - 1, 2)

    # 5: Enforce match overlap constraints
    print("  Adding match overlap constraints... ", file=sys.stderr, end="")
    zone_indices = list(range(len(proto_round[0])))
    round_num_pairs = []
    for earlier_round_num in range(num_rounds - 1):
        for later_round_num in range(earlier_round_num + 1, num_rounds):
            round_num_pairs.append((earlier_round_num, later_round_num))

    match_pairs = []
    for earlier_match in proto_round:
        for later_match in proto_round:
            match_pairs.append((earlier_match, later_match))

    round_and_match_quads = [
        (earlier_round_num, earlier_match, later_round_num, later_match)
        for earlier_round_num, later_round_num in round_num_pairs
        for earlier_match, later_match in match_pairs
    ]

    team_combinations = list(itertools.combinations(teams, forbid_team_overlap))
    zone_permutations = list(itertools.permutations(zone_indices, forbid_team_overlap))

    for (
        (
            earlier_round_num,
            earlier_match,
            later_round_num,
            later_match,
        ),
        real_team_mix,
        early_zones,
        late_zones,
    ) in tqdm.tqdm(
        itertools.product(
            round_and_match_quads,
            team_combinations,
            zone_permutations,
            zone_permutations,
        ),
        total=len(round_and_match_quads)
        * len(team_combinations)
        * len(zone_permutations)
        * len(zone_permutations),
    ):
        assigned_early = z3.And(
            *[
                team_to_pseudo_team[team_number, earlier_round_num]
                == earlier_match[zone_index]
                for team_number, zone_index in zip(real_team_mix, early_zones)
            ]
        )
        assigned_late = z3.And(
            *[
                team_to_pseudo_team[team_number, later_round_num]
                == later_match[zone_index]
                for team_number, zone_index in zip(real_team_mix, late_zones)
            ]
        )
        solver.add(
            z3.Implies(
                assigned_early,
                z3.Not(assigned_late),
            )
        )
    print(f"done, {len(solver.assertions())} constraints", file=sys.stderr)

    # Solve.
    print("Running solver...", file=sys.stderr)
    result = solver.check()
    if result != z3.sat:
        raise ValueError("Unable to solve")

    model = solver.model()

    final_schedule = []

    for round_num in range(num_rounds):
        pseudo_team_to_team = {
            model.evaluate(team_to_pseudo_team[team_num, round_num]).as_long(): team_num
            for team_num in teams
        }
        for match in proto_round:
            assigned_match = [
                pseudo_team_to_team[pseudo_team_num] for pseudo_team_num in match
            ]
            final_schedule.append(assigned_match)

    # breakpoint()

    return final_schedule
