"""Letterbox: pad an IMAGE batch so width and height fit a video model's size rule."""

import torch
import torch.nn.functional as F

from ._common import CATEGORY_VIDEO

# Width/height multiples, from each model's latent node in ComfyUI.
SIZE_PRESETS = {
    "LTX / LTX-2 two-stage (64)": 64,  # stage 1 at half size still lands on 32
    "LTX / LTX-2 (32)": 32,
    "MiniMax H3 (32)": 32,
    "Wan 2.1 / 2.2 (16)": 16,
    "HunyuanVideo (16)": 16,
    "Kandinsky 5 (16)": 16,
    "Cosmos (16)": 16,
    "Mochi (16)": 16,
}
CUSTOM = "custom"
SIZE_OPTIONS = list(SIZE_PRESETS) + [CUSTOM]
PAD_COLORS = {"black": 0.0, "gray": 0.5, "white": 1.0, "edge": None}  # edge repeats border pixels
POSITIONS = ["center", "top_left"]

# Custom socket type: a dict describing one letterbox, passed to Remove Letterbox.
LETTERBOX_INFO = "FLOMFY_LETTERBOX"


def round_up(value, multiple):
    return -(-value // multiple) * multiple


def letterbox_padding(width, height, multiple, position="center"):
    """(left, top, right, bottom) padding that brings width and height up to a multiple."""
    pad_w = round_up(width, multiple) - width
    pad_h = round_up(height, multiple) - height
    if position == "top_left":
        return 0, 0, pad_w, pad_h
    left, top = pad_w // 2, pad_h // 2  # odd remainder goes right / bottom
    return left, top, pad_w - left, pad_h - top


def pad_images(images, left, top, right, bottom, color):
    """Pad (B, H, W, C) images; returns the images and a (B, H, W) mask that is 1 on the bars."""
    b, h, w, _ = images.shape
    mask = torch.zeros((b, h + top + bottom, w + left + right), dtype=torch.float32, device=images.device)
    if not (left or top or right or bottom):
        return images, mask
    x = images.movedim(-1, 1)
    value = PAD_COLORS[color]
    if value is None:
        x = F.pad(x, (left, right, top, bottom), mode="replicate")
    else:
        x = F.pad(x, (left, right, top, bottom), mode="constant", value=value)
    mask[:] = 1.0
    mask[:, top:top + h, left:left + w] = 0.0
    return x.movedim(1, -1), mask


class Letterbox:
    """Pad an IMAGE batch with bars so its size fits the target video model (no scaling)."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "size_rule": (SIZE_OPTIONS, {
                    "default": SIZE_OPTIONS[0],
                    "tooltip": "Width and height are padded up to a multiple of this. "
                               "'custom' uses custom_multiple.",
                }),
                "pad_color": (list(PAD_COLORS), {
                    "default": "black",
                    "tooltip": "Bar color. 'edge' repeats the border pixels instead.",
                }),
                "position": (POSITIONS, {
                    "default": "center",
                    "tooltip": "center: bars split on both sides. top_left: bars only right and bottom.",
                }),
                "custom_multiple": ("INT", {
                    "default": 64, "min": 1, "max": 1024,
                    "tooltip": "Used when size_rule is 'custom'.",
                }),
            }
        }

    # letterbox_info is last so links saved before it existed keep their slots.
    RETURN_TYPES = ("IMAGE", "MASK", "INT", "INT", "INT", "INT", "INT", "INT", LETTERBOX_INFO)
    RETURN_NAMES = ("image", "bars_mask", "original_width", "original_height",
                    "width", "height", "pad_left", "pad_top", "letterbox_info")
    FUNCTION = "run"
    CATEGORY = CATEGORY_VIDEO

    def run(self, image, size_rule, pad_color, position, custom_multiple=64):
        multiple = custom_multiple if size_rule == CUSTOM else SIZE_PRESETS[size_rule]
        h, w = image.shape[1], image.shape[2]
        left, top, right, bottom = letterbox_padding(w, h, multiple, position)
        out, mask = pad_images(image, left, top, right, bottom, pad_color)
        ow, oh = w + left + right, h + top + bottom
        # Shown on the node by web/flomfy.js.
        ui = {"flomfy_size": [w, h, ow, oh, left, top]}
        info = {"original_width": w, "original_height": h, "width": ow, "height": oh,
                "pad_left": left, "pad_top": top}
        return {"ui": ui, "result": (out, mask, w, h, ow, oh, left, top, info)}


def crop_box(info, width, height):
    """(left, top, crop_width, crop_height) of the original picture inside an image of
    width x height, scaling the letterbox when the image was resized since padding."""
    sx = width / info["width"]
    sy = height / info["height"]
    left = min(max(round(info["pad_left"] * sx), 0), width - 1)
    top = min(max(round(info["pad_top"] * sy), 0), height - 1)
    crop_w = min(max(round(info["original_width"] * sx), 1), width - left)
    crop_h = min(max(round(info["original_height"] * sy), 1), height - top)
    return left, top, crop_w, crop_h


class RemoveLetterbox:
    """Crop the bars Flomfy Letterbox added. Works on resized results too (stage 1 at half
    size, upscaled output): the crop is scaled to the incoming image."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "letterbox_info": (LETTERBOX_INFO, {
                    "tooltip": "Link from the letterbox_info output of Flomfy Letterbox.",
                }),
            }
        }

    RETURN_TYPES = ("IMAGE", "INT", "INT")
    RETURN_NAMES = ("image", "width", "height")
    FUNCTION = "run"
    CATEGORY = CATEGORY_VIDEO

    def run(self, image, letterbox_info):
        h, w = image.shape[1], image.shape[2]
        left, top, cw, ch = crop_box(letterbox_info, w, h)
        out = image[:, top:top + ch, left:left + cw]
        ui = {"flomfy_size": [w, h, cw, ch, left, top]}
        return {"ui": ui, "result": (out, cw, ch)}


NODE_CLASS_MAPPINGS = {
    "FlomfyLetterbox": Letterbox,
    "FlomfyRemoveLetterbox": RemoveLetterbox,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "FlomfyLetterbox": "Flomfy Letterbox (pad to size rule)",
    "FlomfyRemoveLetterbox": "Flomfy Remove Letterbox",
}
