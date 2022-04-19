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

    print("  Adding in-match variables... ", file=sys.stderr, end="")
    in_match = {
        (round_num, team_num, match_num): z3.Bool(
            f"in_match_{round_num}_{team_num}_{match_num}"
        )
        for round_num in range(num_rounds)
        for team_num in teams
        for match_num in range(len(proto_round))
    }
    for round_num in range(num_rounds):
        for team_num in teams:
            for match_num, pseudo_teams in enumerate(proto_round):
                # Equality
                solver.add(
                    z3.Or(
                        *[
                            team_to_pseudo_team[team_num, round_num] == pseudo_team
                            for pseudo_team in pseudo_teams
                        ],
                    )
                    == in_match[round_num, team_num, match_num]
                )

    print(f"done, {len(solver.assertions())} constraints", file=sys.stderr)

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
    print("  Adding spacing constraints...", file=sys.stderr)
    for earlier_round_number, early_offset, team_num in tqdm.tqdm(
        itertools.product(
            range(num_rounds - 1),
            range(spacing),
            teams,
        ),
        total=(num_rounds - 1) * spacing * len(teams),
    ):
        later_round_number = earlier_round_number + 1
        for late_offset in range(spacing):
            # If the team is in the (early_offset) match from the end of the
            # earlier round, it cannot be in the (late_offset) match from the
            # start of the later round.
            solver.add(
                z3.Not(
                    z3.And(
                        in_match[
                            earlier_round_number,
                            team_num,
                            len(proto_round) - early_offset - 1,
                        ],
                        in_match[later_round_number, team_num, late_offset],
                    )
                )
            )

    print(f"     ...done, {len(solver.assertions())} constraints", file=sys.stderr)

    forbid_team_overlap = max(len(proto_round[0]) - 1, 2)

    # 5: Enforce match overlap constraints
    print("  Adding match overlap constraints...", file=sys.stderr)
    match_pairings = [
        (
            earlier_round_num,
            earlier_match_num,
            later_round_num,
            later_match_num,
        )
        for earlier_round_num in range(num_rounds - 1)
        for later_round_num in range(earlier_round_num + 1, num_rounds)
        for earlier_match_num in range(len(proto_round))
        for later_match_num in range(len(proto_round))
    ]
    team_groups = list(itertools.combinations(teams, forbid_team_overlap))
    for (
        earlier_round_num,
        earlier_match_num,
        later_round_num,
        later_match_num,
    ), team_group in tqdm.tqdm(
        itertools.product(match_pairings, team_groups),
        total=len(match_pairings) * len(team_groups),
    ):
        all_in_early_match = z3.And(
            *[
                in_match[earlier_round_num, team_num, earlier_match_num]
                for team_num in team_group
            ]
        )
        all_in_later_match = z3.And(
            *[
                in_match[later_round_num, team_num, later_match_num]
                for team_num in team_group
            ]
        )
        solver.add(
            z3.Not(
                z3.And(
                    all_in_early_match,
                    all_in_later_match,
                )
            )
        )
    print(f"     ...done, {len(solver.assertions())} constraints", file=sys.stderr)

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
