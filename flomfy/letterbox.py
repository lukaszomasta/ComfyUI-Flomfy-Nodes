"""Letterbox: pad an IMAGE batch so width and height fit a video model's size rule."""

import torch

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


def bars_mask(frames, height, width, left, top, right, bottom, device):
    """(frames, H, W) mask, 1 on the bars. One frame expanded over the batch: the bars are
    the same on every frame, so no per-frame memory is used."""
    mask = torch.ones((1, height, width), dtype=torch.float32, device=device)
    mask[:, top:height - bottom, left:width - right] = 0.0
    return mask.expand(frames, -1, -1)


def conform(images, frames, left, top, right, bottom, color):
    """Pad (B, H, W, C) images with bars and fit them to `frames` frames (cut, or hold the
    last frame) in one allocation. Returns the images and the bars mask."""
    b, h, w, c = images.shape
    oh, ow = h + top + bottom, w + left + right
    mask = bars_mask(frames, oh, ow, left, top, right, bottom, images.device)
    if frames == b and not (left or top or right or bottom):
        return images, mask
    n = min(b, frames)
    out = torch.empty((frames, oh, ow, c), dtype=images.dtype, device=images.device)
    out[:n, top:top + h, left:left + w] = images[:n]
    value = PAD_COLORS[color]
    if value is None:  # edge: columns first, then full rows, so the corners repeat too
        if left:
            out[:n, top:top + h, :left] = out[:n, top:top + h, left:left + 1]
        if right:
            out[:n, top:top + h, left + w:] = out[:n, top:top + h, left + w - 1:left + w]
        if top:
            out[:n, :top] = out[:n, top:top + 1]
        if bottom:
            out[:n, top + h:] = out[:n, top + h - 1:top + h]
    else:
        out[:n, :top] = value
        out[:n, top + h:] = value
        out[:n, top:top + h, :left] = value
        out[:n, top:top + h, left + w:] = value
    if frames > n:
        out[n:] = out[n - 1]
    return out, mask


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
        out, mask = conform(image, image.shape[0], left, top, right, bottom, pad_color)
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
