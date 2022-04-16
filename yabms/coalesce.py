"""
Coalesce proto-rounds.

Having built a valid proto-round, we can coalesce multiple
proto-rounds together to build a single schedule.
"""

import sys

import tqdm
import z3


def _add_round(proto_round, confirmed, *, spacing=1):
    num_teams = len({y for x in proto_round for y in x})
    teams = list(range(num_teams))

    solver = z3.Solver()

    team_assignment = {team: z3.Int(f"team-{team}") for team in teams}

    # 1: Range constraints. Each assignment must be a team number.
    for assignment in team_assignment.values():
        solver.add(assignment >= min(teams))
        solver.add(assignment <= max(teams))

    # 2: Bijection constraints. Each team must appear exactly once.
    values = list(team_assignment.values())
    for ix, left_assignment in enumerate(values[:-1]):
        for right_assignment in values[ix + 1 :]:
            solver.add(left_assignment != right_assignment)
    del values

    # 3: Spacing constraints. Teams must have at least the spacing gap
    # between appearances. We need only implement this for the first
    # few matches, as the spacing within the proto-round is already
    # enforced.
    for ix, match in enumerate(proto_round[:spacing]):
        conflicting_teams = {
            team for true_match in confirmed[-spacing + ix :] for team in true_match
        }
        for pseudo_team in match:
            for conflicting_team in conflicting_teams:
                solver.add(team_assignment[pseudo_team] != conflicting_team)

    # 4: Duplication constraints. The assignment cannot produce any fully
    # duplicated matches.
    for true_match in confirmed:
        for provisional_match in proto_round:
            match_terms = []
            for true_team, pseudo_team in zip(true_match, provisional_match):
                match_terms.append(team_assignment[pseudo_team] == true_team)
            exact_match = z3.And(*match_terms)
            solver.add(z3.Not(exact_match))

    # TODO: 5: Facing constraints.

    result = solver.check()

    if result != z3.sat:
        raise ValueError("Solver failed to find a team assignment.")

    model = solver.model()

    true_team_assignments = {
        pseudo_team: model[team_assignment[pseudo_team]].as_long()
        for pseudo_team in team_assignment
    }

    new_round = [
        [true_team_assignments[pseudo_team] for pseudo_team in match]
        for match in proto_round
    ]

    return confirmed + new_round


def coalesce(proto_round, num_rounds, *, spacing=1):
    """Coalesce a proto-round sequence into a schedule."""
    # For each round, we need to select a team assignment of
    # the proto-round which preserves the spacing window.
    confirmed = proto_round

    print("Coalescing proto-rounds into full schedule...", file=sys.stderr)
    for _ in tqdm.trange(1, num_rounds):
        # For each round, we need to select a team assignment of
        # the proto-round which preserves the spacing window.
        confirmed = _add_round(proto_round, confirmed, spacing=spacing)

    return confirmed
