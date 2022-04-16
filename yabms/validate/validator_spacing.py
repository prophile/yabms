"""Validator: teams have sufficient gap between matches."""

from .validator_equal_appearances import validate_equal_appearances
from .validators import error, validator

# TODO: Parameterize this.
MIN_SPACING = 1


@validator("spacing", after=[validate_equal_appearances])
def validate_spacing(schedule):
    """Validate that teams have sufficient gap between matches."""
    window_size = MIN_SPACING + 1

    for ix, match in enumerate(schedule[: -window_size + 1]):
        for team in match:
            for other_match in schedule[ix + 1 : ix + window_size]:
                if team in other_match:
                    yield error(
                        "spacing",
                        f"Team {team} appears in match {ix} and {ix + window_size}",
                    )
