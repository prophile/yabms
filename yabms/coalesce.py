"""
Coalesce proto-rounds.

Having built a valid proto-round, we can coalesce multiple
proto-rounds together to build a single schedule.
"""

import sys

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
    for allocation in team_to_pseudo_team.values():
        solver.add(allocation >= min_team)
        solver.add(allocation <= max_team)

    # 2: Enforce round bijection: each allocation is different in each round
    for round_num in range(num_rounds):
        solver.add(
            z3.Distinct(
                *[team_to_pseudo_team[team_num, round_num] for team_num in teams]
            )
        )

    # 3: Enforce different allocation in each round
    for team_num in teams:
        solver.add(
            z3.Distinct(
                *[
                    team_to_pseudo_team[team_num, round_num]
                    for round_num in range(num_rounds)
                ]
            )
        )

    # 4: Enforce spacing constraints
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

    # 5: Enforce facing constraints
    optimal_facings = _total_facings_per_team_pair(
        match_size=len(proto_round[0]),
        num_matches=len(proto_round) * num_rounds,
        num_teams=len(teams),
    )
    min_facings = optimal_facings - 2
    max_facings = optimal_facings + 3
    if min_facings < 0:
        min_facings = 0
    facing_vars = []
    print(
        f"Facing bounds: at least {min_facings}, at most {max_facings}", file=sys.stderr
    )
    for ix, left_team in enumerate(teams):
        for right_team in teams[ix + 1 :]:
            # How many times do they face?
            facing_count = z3.Int(f"facing_{left_team}_{right_team}")
            facings = 0
            for round_num in range(num_rounds):
                for match in proto_round:
                    for left_zone in match:
                        for right_zone in match:
                            if left_zone == right_zone:
                                continue
                            is_facing = z3.And(
                                team_to_pseudo_team[left_team, round_num] == left_zone,
                                team_to_pseudo_team[right_team, round_num]
                                == right_zone,
                            )
                            facings += z3.If(is_facing, 1, 0)
            solver.add(facing_count == z3.simplify(facings))
            solver.add(facing_count >= min_facings)
            solver.add(facing_count <= max_facings)
            facing_vars.append(facing_count)

    # 6: Enforce match uniqueness constraints
    # TODO: How?

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
