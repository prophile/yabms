"""Make sure all validators are registered."""


def register_all_validators():
    """Make sure all validators are registered."""
    from . import validator_dupes, validator_size  # noqa: F401
