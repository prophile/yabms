"""Schedule validators."""

_VALIDATORS = []

# A validator is a generator which yields warnings and errors.
# The generator can return False to stop the validation process.


def validator(name, *, after=None):
    """
    Decorate validators.

    To specify an order for validators, use the `after` keyword argument
    with a list of other validators (NB validators, not names) that must
    have already run.
    """
    # For the `after` keyword, we actually just check they're not names:
    # the fact that the concrete objects have already had validator()
    # called means they are already earlier in the sequence.
    if after is not None:
        for other in after:
            if isinstance(other, str):
                raise ValueError(f"{other!r} is not a validator, only a name")
            if not hasattr(other, "_validator_name"):
                raise ValueError(f"{other!r} is not a registered validator")

    def decorator(func):
        func._validator_name = name
        _VALIDATORS.append(func)
        return func

    return decorator


def error(message):
    """
    Produce an error in a validator to be emitted.

    Usage:
    >>> yield error("No teams in zone 1")
    """
    return "error", message


def warning(message):
    """
    Produce a warning in a validator to be emitted.

    Usage:
    >>> yield warning("Team 5 has fewer matches than team 6")
    """
    return "warning", message


def _run_validator(validator, schedule, warnings, errors):
    """Run a single validator."""
    generator = validator(schedule)
    try:
        while True:
            level, message = next(generator)
            if level == "error":
                errors.append(message)
            elif level == "warning":
                warnings.append(message)
            else:
                raise ValueError(f"Unknown level {level!r}")
    except StopIteration as e:
        if e.value is False:
            return False
    return True


def run_validators(schedule):
    """
    Run all validators on a schedule.

    Returns a tuple of (warnings, errors).
    """
    warnings = []
    errors = []

    # Early-exit if the schedule is blank
    if not schedule:
        return [], ["No matches in schedule"]

    for validator in _VALIDATORS:
        if not _run_validator(validator, schedule, warnings, errors):
            break
    return warnings, errors
