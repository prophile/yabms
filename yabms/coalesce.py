"""
Coalesce proto-rounds.

Having built a valid proto-round, we can coalesce multiple
proto-rounds together to build a single schedule.
"""

import itertools
import sys
import random

import tqdm
import z3


def _z3_lookup(table, key, default=None):
    """Build an ITE chain for Z3 to look up a value in a dict."""
    # If we have no default, choose one item from the table arbitrarily.
    table = dict(table)

    if isinstance(key, int):
        # ????
        # raise AssertionError
        return table.get(key, default)

    if default is None:
        try:
            _, default = table.popitem()
        except KeyError:
            raise ValueError("No default value provided and no table items")

    expression = default

    while table:
        this_key, this_value = table.popitem()
        expression = z3.If(key == this_key, this_value, expression)

    return z3.simplify(expression)


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

    # 5: Facing constraints. The maximum distance between the facing count of any
    # two teams is 3.
    existing_facings = {
        (left_team, right_team): 0
        for ix, left_team in enumerate(teams[:-1])
        for right_team in teams[ix + 1 :]
    }
    for true_match in confirmed:
        true_match = sorted(true_match)
        for ix, left_team in enumerate(true_match[:-1]):
            for right_team in true_match[ix + 1 :]:
                existing_facings[left_team, right_team] += 1

    facings_in_order = sorted(
        existing_facings.keys(),
        key=lambda x: (existing_facings[x], random.random()),
    )

    def ensure_facing(a, b):
        assert a != b
        has_facing = []

        for match in proto_round:
            for left_team in match:
                for right_team in match:
                    if left_team is right_team:
                        continue
                    has_facing.append(
                        z3.And(
                            team_assignment[left_team] == a,
                            team_assignment[right_team] == b,
                        ),
                    )

        solver.add(z3.Or(*has_facing))

    # Ensure the bottom 5 percentile get a facing in this round.
    for a, b in facings_in_order[: 3 * len(facings_in_order) // 100]:
        ensure_facing(a, b)

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
