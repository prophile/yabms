"""Make sure all validators are registered."""


def register_all_validators():
    """Make sure all validators are registered."""
    from . import (  # noqa: F401
        validator_dupes,
        validator_equal_appearances,
        validator_rerun,
        validator_size,
        validator_zone_distribution,
    )
