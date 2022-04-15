"""
Proto-rounds.

These are 'prototype' rounds which may be duplicated to form a
complete match schedule. A prototype round only has an abstract
assignment of a 'team index' to a match. A complete schedule has
to populate the proto-rounds with assignments of actual teams, and
permute the zones.
"""

import os
import os.path
import pickle
import sys

import z3


def _get_cache_root():
    if sys.platform in ("freebsd", "linux", "darwin"):
        return "/tmp"
    else:
        return os.getcwd()


def _get_cache_dir():
    root = _get_cache_root()
    cache_dir = os.path.join(root, "yabms-cache")
    try:
        os.mkdir(cache_dir)
    except FileExistsError:
        pass
    return cache_dir


def _get_cache_file(key):
    cache_dir = _get_cache_dir()
    cache_file = os.path.join(cache_dir, f"{key}.pkl")
    return cache_file


def _get_cache(key):
    cache_file = _get_cache_file(key)
    try:
        with open(cache_file, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return None


def _set_cache(key, value):
    cache_file = _get_cache_file(key)
    with open(cache_file, "wb") as f:
        pickle.dump(value, f, protocol=pickle.HIGHEST_PROTOCOL)


def build_proto_round(
    *,
    num_teams: int,
    appearances_per_round: int,
    num_zones: int,
    spacing: int,
):
    """Construct a single proto-round."""
    # Since this step takes a Bloody Age™, we pull this from a
    # cache if at all possible.
    cache_key = f"pround-{num_teams}-{appearances_per_round}-{num_zones}-{spacing}"
    if proto_round := _get_cache(cache_key):
        print("Using cached proto-round", file=sys.stderr)
        return proto_round
    # Otherwise, build it.
    proto_round = _build_proto_round(
        num_teams=num_teams,
        appearances_per_round=appearances_per_round,
        num_zones=num_zones,
        spacing=spacing,
    )
    _set_cache(cache_key, proto_round)
    return proto_round


def _build_proto_round(
    *, num_teams: int, appearances_per_round: int, num_zones: int, spacing: int
):
    solver = z3.Solver()

    num_matches = (num_teams * appearances_per_round + (num_zones - 1)) // num_zones
    print(f"Solver for {num_matches} matches", file=sys.stderr)

    print("Building constraints...", file=sys.stderr)
    # Variables for all the match assignments.
    match_assignments = {
        (match_number, zone_number): z3.Int(f"match-{match_number}-{zone_number}")
        for match_number in range(num_matches)
        for zone_number in range(num_zones)
    }

    def num_appearances_in_window(team, window_start=0, window_end=-1):
        """Count the number of appearances of a team in a window."""
        if window_end < 0:
            window_end = num_matches
        return sum(
            z3.If(match_assignments[match, zone] == team, 1, 0)
            for match in range(window_start, window_end)
            for zone in range(num_zones)
        )

    # 1: Range constraints. Each assignment must be a team number.
    for appearance in match_assignments.values():
        solver.add(appearance >= 0)
        solver.add(appearance < num_teams)

    # 2: Order constraints. Each match has teams in strictly increasing
    # order. This necessarily implies uniqueness within a match.
    for match_number in range(num_matches):
        for zone_number in range(num_zones - 1):
            solver.add(
                match_assignments[match_number, zone_number]
                < match_assignments[match_number, zone_number + 1]
            )

    # 3: Count constraints. Each team must appear exactly the right
    # number of times in the schedule.
    for team_number in range(num_teams):
        solver.add(num_appearances_in_window(team_number) == appearances_per_round)

    # 4: Spacing constraints. Teams must have at least the spacing gap
    # between appearances. We implement this as a sliding (spacing + 1)
    # window where team appearances must be unique.
    if spacing > 0 and appearances_per_round > 1:
        for window_start in range(num_matches - spacing):
            window_end = window_start + spacing + 1
            for team_number in range(num_teams):
                solver.add(
                    num_appearances_in_window(team_number, window_start, window_end)
                    <= 1
                )

    # 5: Facing constraints. Each team may face any given other team in this
    # proto-round at most once. This is not relevant if there is only one
    # appearance per team.
    if appearances_per_round > 1:
        for left_team in range(num_teams - 1):
            for right_team in range(left_team + 1, num_teams):
                times_faced = 0
                for left_zone in range(num_zones - 1):
                    for right_zone in range(left_zone + 1, num_zones):
                        for match_number in range(num_matches):
                            is_facing = z3.And(
                                (
                                    match_assignments[match_number, left_zone]
                                    == left_team
                                ),
                                (
                                    match_assignments[match_number, right_zone]
                                    == right_team
                                ),
                            )
                            times_faced += z3.If(is_facing, 1, 0)
                solver.add(times_faced <= 1)

    print("Solving...", file=sys.stderr)
    result = solver.check()

    if result != z3.sat:
        raise ValueError("Solver failed to find a solution.")

    model = solver.model()

    matches = []
    for match_number in range(num_matches):
        match = []
        for zone_number in range(num_zones):
            match.append(
                model.eval(match_assignments[(match_number, zone_number)]).as_long()
            )
        matches.append(match)

    return matches
