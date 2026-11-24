"""Shared helpers for Flomfy nodes."""

# Kept as "utils/ocio" so the nodes stay where existing users expect them.
CATEGORY_OCIO = "utils/ocio"
CATEGORY_LTX = "utils/ltx"


def snap(v, multiple):
    """Round v to the nearest multiple (at least one multiple)."""
    return max(multiple, int(round(v / float(multiple))) * multiple)
