"""YABMS command-line interface."""

import argparse
import sys

import pkg_resources


def get_version():
    """
    Extract the current version number.

    This reaches into `pkg_resources` to find out what was installed.
    In this way we avoid duplication.
    """
    return pkg_resources.require("yabms")[0].version


def argument_parser():
    """Get the parser for command-line arguments."""
    parser = argparse.ArgumentParser(description="Yet Another Bloody Match Scheduler")
    parser.add_argument(
        "-V", "--version", action="version", version=f"%(prog)s {get_version()}"
    )
    parser.add_argument(
        "-n", "--num-teams", type=int, default=8, help="number of teams to schedule"
    )
    parser.add_argument(
        "-r", "--rounds", type=int, default=3, help="number of rounds to schedule"
    )
    parser.add_argument(
        "-a",
        "--appearances",
        type=int,
        default=1,
        help="number of appearances per team",
    )
    parser.add_argument(
        "-z", "--zones", type=int, default=4, help="number of zones per match"
    )
    parser.add_argument(
        "-s",
        "--spacing",
        type=int,
        default=1,
        help="number of gaps for any given team between matches",
    )
    return parser


def main(args=sys.argv[1:]):
    """Run as main entry point."""
    options = argument_parser().parse_args(args)
    print(options)
    print(f"{get_version()}")
