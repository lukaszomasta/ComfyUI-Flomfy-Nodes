"""Run from the repo root: python -m pytest tests"""

import os
import sys

import pytest
import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flomfy import NODE_CLASS_MAPPINGS  # noqa: E402
from flomfy.frames import PadToFrameFormula, fit_down, fit_up, parse_formula  # noqa: E402
from flomfy.ocio import OCIOInfoParse  # noqa: E402


def test_node_ids_are_stable():
    assert {"FlomfyOCIOInfoParse", "FlomfyFramePadder"} <= set(NODE_CLASS_MAPPINGS)


@pytest.mark.parametrize("text,expected", [
    ("8n+1", (8, 1)), ("4n+1", (4, 1)), ("16n", (16, 0)), ("n", (1, 0)),
    ("8*n+1", (8, 1)), ("8n-3", (8, -3)), ("8 n + 1", (8, 1)), ("8N+1", (8, 1)),
])
def test_parse_formula(text, expected):
    assert parse_formula(text) == expected


@pytest.mark.parametrize("text", ["", "8x+1", "0n+1", "abc"])
def test_parse_formula_rejects(text):
    with pytest.raises(ValueError):
        parse_formula(text)


def test_fit():
    assert fit_up(10, 8, 1) == 17
    assert fit_up(17, 8, 1) == 17
    assert fit_down(10, 8, 1) == 9
    assert fit_down(0, 8, 1) is None


def _frames(n):
    return torch.arange(n, dtype=torch.float32).view(n, 1, 1, 1).expand(n, 2, 2, 3).clone()


def test_hold_pad():
    out, length, orig, pad = PadToFrameFormula().pad(_frames(10), "8n+1", "hold_pad")
    assert (length, orig, pad) == (17, 10, 7)
    assert out.shape[0] == 17 and torch.all(out[10:] == 9)


def test_trim_and_fallback():
    out, length, orig, pad = PadToFrameFormula().pad(_frames(10), "8n+1", "trim")
    assert (out.shape[0], length, orig, pad) == (9, 9, 10, -1)
    # Shorter than the smallest valid length: pads instead.
    out, length, _, pad = PadToFrameFormula().pad(_frames(3), "8n+5", "trim")
    assert (length, pad) == (5, 2)


def test_original():
    out, length, orig, pad = PadToFrameFormula().pad(_frames(10), "8n+1", "original")
    assert (out.shape[0], length, orig, pad) == (10, 10, 10, 0)


def test_ocio_info_parse():
    info = "shot_010.####.exr  97 frame(s)  frames [1001-1097]  3840x2160"
    assert OCIOInfoParse().parse(info, 2) == (97, 1001, 1097, 3840, 2160, 1920, 1088)
    assert OCIOInfoParse().parse("nothing here", 2) == (0, 0, 0, 0, 0, 0, 0)
