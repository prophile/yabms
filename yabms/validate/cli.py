"""YABMS validator command-line interface."""

import argparse
import sys

from ..cli import get_version
from . import validator_registry, validators


def argument_parser():
    """Parser for the command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Yet Another Bloody Match Scheduler validator"
    )
    parser.add_argument(
        "-V", "--version", action="version", version=f"%(prog)s {get_version()}"
    )
    parser.add_argument(
        "input",
        nargs="?",
        type=argparse.FileType("r"),
        default=sys.stdin,
        help="input file (default: stdin)",
    )
    parser.add_argument(
        "--separator",
        type=str,
        default="|",
        help="separator for input file (default: '|')",
    )
    return parser


def main(args=sys.argv[1:]):
    """Run as main entry point."""
    options = argument_parser().parse_args(args)

    matches = []

    with options.input as f:
        for line in f:
            matches.append(line.strip().split(options.separator))

    validator_registry.register_all_validators()

    warnings, errors = validators.run_validators(matches)

    for code, warning in warnings:
        print(f"W {code}: {warning}")
    for code, error in errors:
        print(f"E {code}: {error}")

    print(f"{len(warnings)} warnings, {len(errors)} errors")

    if errors:
        print("Validation failed.")
        sys.exit(1)
    else:
        print("Validation succeeded.")
        sys.exit(0)
