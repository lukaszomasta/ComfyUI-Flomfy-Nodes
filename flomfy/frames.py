"""Frame-count nodes: fit an IMAGE batch to a length of the form a*n+b."""

import math
import re

import torch

from ._common import CATEGORY_OCIO

LENGTH_MODES = ["hold_pad", "trim", "original"]

# Frame-count rules, taken from each model's latent node in ComfyUI
# (latent frames = (length - 1) // a + 1, or MiniMax H3's own 17n+5 alignment).
FORMULA_PRESETS = {
    "LTX / LTX-2 (8n+1)": "8n+1",
    "Wan 2.1 / 2.2 (4n+1)": "4n+1",
    "HunyuanVideo (4n+1)": "4n+1",
    "Kandinsky 5 (4n+1)": "4n+1",
    "Cosmos Predict2 (4n+1)": "4n+1",
    "Cosmos 1 (8n+1)": "8n+1",
    "Mochi (6n+1)": "6n+1",
    "MiniMax H3 (17n+5)": "17n+5",
}
CUSTOM = "custom"
FORMULA_OPTIONS = list(FORMULA_PRESETS) + [CUSTOM]

# Accepts: 8n+1, 4n+1, 16n, n, 8*n+1, 8n-3, "8 n + 1", 8N+1
_FORMULA_RE = re.compile(r"^\s*(\d*)\s*\*?\s*n\s*(?:([+-])\s*(\d+))?\s*$", re.IGNORECASE)


def parse_formula(formula):
    m = _FORMULA_RE.match(formula or "")
    if not m:
        raise ValueError(
            f"Invalid frame formula '{formula}'. Use the form a*n+b, "
            f"for example 8n+1, 4n+1, 16n or n."
        )
    a = int(m.group(1)) if m.group(1) else 1
    if a < 1:
        raise ValueError(f"Invalid frame formula '{formula}': multiplier must be >= 1.")
    b = int(m.group(3)) if m.group(3) else 0
    if m.group(2) == "-":
        b = -b
    return a, b


def resolve_formula(formula, custom_formula="8n+1"):
    """Turn the dropdown value into an a*n+b formula string.

    A value that is neither a preset nor "custom" is used as a formula itself: workflows
    saved before the dropdown existed store the formula text (e.g. "8n+1") there.
    """
    if formula == CUSTOM:
        return custom_formula
    return FORMULA_PRESETS.get(formula, formula)


def smallest_valid(a, b):
    """Smallest a*k+b that is >= 1 (k >= 0 integer)."""
    k = max(0, math.ceil((1 - b) / a))
    return a * k + b


def fit_up(n, a, b):
    """Smallest a*k+b >= n."""
    k = max(0, math.ceil((n - b) / a))
    return max(a * k + b, smallest_valid(a, b))


def fit_down(n, a, b):
    """Largest a*k+b <= n, or None if no valid length fits."""
    k = math.floor((n - b) / a)
    if k < 0:
        return None
    length = a * k + b
    return length if length >= 1 else None


class PadToFrameFormula:
    """Fit an IMAGE batch to a model's frame-count rule (8n+1 for LTX, 4n+1 for Wan, ...)
    by holding the last frame, trimming, or passing through."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "formula": (FORMULA_OPTIONS, {
                    "default": FORMULA_OPTIONS[0],
                    "tooltip": "Frame-count rule of the target model. 'custom' uses custom_formula.",
                }),
                "length_mode": (LENGTH_MODES, {"default": "hold_pad"}),
                "custom_formula": ("STRING", {
                    "default": "8n+1",
                    "tooltip": "Used when formula is 'custom'. Form a*n+b, e.g. 8n+1, 4n+1, 16n.",
                }),
            }
        }

    RETURN_TYPES = ("IMAGE", "INT", "INT", "INT")
    RETURN_NAMES = ("images", "length", "original_length", "pad_frames")
    FUNCTION = "pad"
    CATEGORY = CATEGORY_OCIO

    @classmethod
    def VALIDATE_INPUTS(cls, formula):
        # Listing `formula` here replaces ComfyUI's dropdown check, so old workflows that
        # saved a formula string (e.g. "8n+1") still run.
        if formula in FORMULA_PRESETS or formula == CUSTOM:
            return True
        try:
            parse_formula(formula)
        except ValueError as e:
            return str(e)
        return True

    def pad(self, images, formula, length_mode, custom_formula="8n+1"):
        n = images.shape[0]
        if length_mode == "original":
            return (images, n, n, 0)

        a, b = parse_formula(resolve_formula(formula, custom_formula))

        if length_mode == "trim":
            target = fit_down(n, a, b)
            if target is not None:
                # pad_frames is negative when frames were removed
                return (images[:target], target, n, target - n)
            # Clip shorter than the smallest valid length: fall through to padding.

        target = fit_up(n, a, b)
        extra = target - n
        if extra > 0:
            hold = images[-1:].repeat(extra, 1, 1, 1)
            images = torch.cat([images, hold], dim=0)
        return (images, target, n, extra)


NODE_CLASS_MAPPINGS = {
    "FlomfyFramePadder": PadToFrameFormula,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "FlomfyFramePadder": "Flomfy Frame Padder (hold last)",
}
