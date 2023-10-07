"""Utilities for the application."""


def _convert_seconds_to_time(seconds: int) -> str:
    """Convert a number of seconds to a HH:MM:SS time.

    Args:
        seconds (int): Time in seconds.

    Returns:
        str: Formatted time.
    """
    mins, rem_s = divmod(seconds, 60)
    hours, mins = divmod(mins, 60)
    return f"{hours:02}:{mins:02}:{rem_s:02}"
