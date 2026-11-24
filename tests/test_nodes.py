"""Run from the repo root: python -m pytest tests"""

import os
import sys

import pytest
import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flomfy import NODE_CLASS_MAPPINGS  # noqa: E402
from flomfy.frames import (  # noqa: E402
    FORMULA_PRESETS, PadToFrameFormula, fit_down, fit_up, parse_formula, resolve_formula,
)
from flomfy.letterbox import Letterbox, RemoveLetterbox, crop_box, letterbox_padding  # noqa: E402
from flomfy.ltx import LTXStage1Helper, stage1_size  # noqa: E402
from flomfy.ocio import OCIOInfoParse  # noqa: E402


def test_node_ids_are_stable():
    assert {"FlomfyOCIOInfoParse", "FlomfyFramePadder", "FlomfyLTXStage1Helper", "FlomfyLetterbox", "FlomfyRemoveLetterbox"} <= set(NODE_CLASS_MAPPINGS)


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
    assert OCIOInfoParse().parse(info) == (97, 1001, 1097, 3840, 2160)
    assert OCIOInfoParse().parse("nothing here") == (0, 0, 0, 0, 0)


def test_stage1_size():
    assert stage1_size(3840, 2160, 2) == (1920, 1088)
    assert stage1_size(1920, 1080, 1) == (1920, 1088)
    assert stage1_size(100, 40, 4) == (32, 32)


def test_ltx_stage1_helper_passes_image_through():
    image = torch.rand(3, 216, 384, 3)
    out, w, h, mult = LTXStage1Helper().run(image, 2)
    assert (w, h, mult) == (192, 96, 2)
    assert out is image


def test_presets_parse():
    for label, formula in FORMULA_PRESETS.items():
        assert resolve_formula(label) == formula
        parse_formula(formula)


def test_preset_padding():
    pad = PadToFrameFormula().pad
    assert pad(_frames(10), "LTX / LTX-2 (8n+1)", "hold_pad")[1] == 17
    assert pad(_frames(10), "Wan 2.1 / 2.2 (4n+1)", "hold_pad")[1] == 13
    assert pad(_frames(10), "Mochi (6n+1)", "hold_pad")[1] == 13
    assert pad(_frames(100), "MiniMax H3 (17n+5)", "hold_pad")[1] == 107
    assert pad(_frames(100), "MiniMax H3 (17n+5)", "trim")[1] == 90
    assert pad(_frames(3), "MiniMax H3 (17n+5)", "hold_pad")[1] == 5


def test_custom_and_legacy_formula():
    pad = PadToFrameFormula().pad
    assert pad(_frames(10), "custom", "hold_pad", "16n")[1] == 16
    # Workflows saved before the dropdown store the formula text itself.
    assert pad(_frames(10), "8n+1", "hold_pad")[1] == 17
    assert PadToFrameFormula.VALIDATE_INPUTS("8n+1") is True
    assert PadToFrameFormula.VALIDATE_INPUTS("Mochi (6n+1)") is True
    assert isinstance(PadToFrameFormula.VALIDATE_INPUTS("nonsense"), str)


def test_letterbox_padding():
    assert letterbox_padding(1920, 1080, 64) == (0, 4, 0, 4)
    assert letterbox_padding(1920, 1080, 32) == (0, 4, 0, 4)
    assert letterbox_padding(1920, 1080, 16) == (0, 4, 0, 4)
    assert letterbox_padding(1000, 563, 64) == (12, 6, 12, 7)
    assert letterbox_padding(1000, 563, 64, "top_left") == (0, 0, 24, 13)
    assert letterbox_padding(1024, 576, 64) == (0, 0, 0, 0)


@pytest.mark.parametrize("color", ["black", "gray", "white", "edge"])
def test_letterbox_node(color):
    image = torch.full((2, 563, 1000, 3), 0.25)
    res = Letterbox().run(image, "LTX / LTX-2 two-stage (64)", color, "center")
    out, mask, w, h, ow, oh, left, top, info = res["result"]
    assert (w, h, ow, oh, left, top) == (1000, 563, 1024, 576, 12, 6)
    assert out.shape == (2, 576, 1024, 3) and mask.shape == (2, 576, 1024)
    assert torch.equal(out[:, top:top + h, left:left + w], image)
    assert mask[:, top:top + h, left:left + w].sum() == 0 and mask[0, 0, 0] == 1
    bar = {"black": 0.0, "gray": 0.5, "white": 1.0, "edge": 0.25}[color]
    assert torch.allclose(out[0, 0, 0], torch.full((3,), bar))
    assert res["ui"]["flomfy_size"] == [1000, 563, 1024, 576, 12, 6]


def test_letterbox_custom_and_noop():
    image = torch.rand(1, 64, 128, 3)
    out, mask, *_ = Letterbox().run(image, "custom", "black", "center", 64)["result"]
    assert out is image and mask.sum() == 0
    out, *_ = Letterbox().run(image, "custom", "black", "center", 100)["result"]
    assert out.shape == (1, 100, 200, 3)


def test_remove_letterbox_round_trip():
    image = torch.rand(2, 563, 1000, 3)
    padded, *_, info = Letterbox().run(image, "LTX / LTX-2 two-stage (64)", "black", "center")["result"]
    res = RemoveLetterbox().run(padded, info)
    out, w, h = res["result"]
    assert (w, h) == (1000, 563) and torch.equal(out, image)
    assert res["ui"]["flomfy_size"] == [1024, 576, 1000, 563, 12, 6]


def test_remove_letterbox_scaled():
    # 1920x1080 -> 1920x1088 (4 px bars); a half-size stage-1 render is 960x544.
    info = Letterbox().run(torch.rand(1, 1080, 1920, 3), "LTX / LTX-2 two-stage (64)",
                           "black", "center")["result"][-1]
    assert crop_box(info, 960, 544) == (0, 2, 960, 540)
    assert crop_box(info, 3840, 2176) == (0, 8, 3840, 2160)
    out, w, h = RemoveLetterbox().run(torch.rand(4, 544, 960, 3), info)["result"]
    assert out.shape == (4, 540, 960, 3) and (w, h) == (960, 540)


def test_remove_letterbox_top_left_and_noop():
    image = torch.rand(1, 563, 1000, 3)
    padded, *_, info = Letterbox().run(image, "LTX / LTX-2 two-stage (64)", "black", "top_left")["result"]
    assert torch.equal(RemoveLetterbox().run(padded, info)["result"][0], image)
    image = torch.rand(1, 64, 128, 3)
    padded, *_, info = Letterbox().run(image, "custom", "black", "center", 64)["result"]
    assert torch.equal(RemoveLetterbox().run(padded, info)["result"][0], image)
