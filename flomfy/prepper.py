"""Image Prepper: Frame Padder and Letterbox in one node, with a single copy of the frames."""

from ._common import CATEGORY_VIDEO
from .frames import FORMULA_OPTIONS, LENGTH_MODES, resolve_formula, target_length
from .letterbox import CUSTOM as CUSTOM_SIZE
from .letterbox import (LETTERBOX_INFO, PAD_COLORS, POSITIONS, SIZE_OPTIONS, SIZE_PRESETS,
                        conform, letterbox_padding)


class ImagePrepper:
    """Fit an IMAGE batch to a video model: frame count (a*n+b) and size (bars, no scaling)."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "frame_rule": (FORMULA_OPTIONS, {
                    "default": FORMULA_OPTIONS[0],
                    "tooltip": "Frame-count rule of the target model. 'custom' uses custom_formula.",
                }),
                "length_mode": (LENGTH_MODES, {
                    "default": "hold_pad",
                    "tooltip": "hold_pad: repeat the last frame up to the next valid length. "
                               "trim: cut to the previous one. original: keep the frame count.",
                }),
                "size_rule": (SIZE_OPTIONS, {
                    "default": SIZE_OPTIONS[0],
                    "tooltip": "Width and height are padded up to a multiple of this. 'custom' uses custom_multiple.",
                }),
                "pad_color": (list(PAD_COLORS), {
                    "default": "edge",
                    "tooltip": "Bar color. 'edge' repeats the border pixels instead.",
                }),
                "position": (POSITIONS, {
                    "default": "center",
                    "tooltip": "center: bars split on both sides. top_left: bars only right and bottom.",
                }),
                "custom_formula": ("STRING", {
                    "default": "8n+1",
                    "tooltip": "Used when frame_rule is 'custom'. Form a*n+b, e.g. 8n+1, 4n+1, 16n.",
                }),
                "custom_multiple": ("INT", {
                    "default": 64, "min": 1, "max": 1024,
                    "tooltip": "Used when size_rule is 'custom'.",
                }),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK", LETTERBOX_INFO, "INT", "INT", "INT", "INT", "INT", "INT")
    RETURN_NAMES = ("image", "bars_mask", "letterbox_info", "original_width", "original_height",
                    "width", "height", "original_length", "length")
    FUNCTION = "run"
    CATEGORY = CATEGORY_VIDEO

    def run(self, image, frame_rule, length_mode, size_rule, pad_color, position,
            custom_formula="8n+1", custom_multiple=64):
        n, h, w = image.shape[0], image.shape[1], image.shape[2]
        frames = target_length(n, resolve_formula(frame_rule, custom_formula), length_mode)
        multiple = custom_multiple if size_rule == CUSTOM_SIZE else SIZE_PRESETS[size_rule]
        left, top, right, bottom = letterbox_padding(w, h, multiple, position)
        out, mask = conform(image, frames, left, top, right, bottom, pad_color)
        ow, oh = w + left + right, h + top + bottom
        info = {"original_width": w, "original_height": h, "width": ow, "height": oh,
                "pad_left": left, "pad_top": top}
        ui = {"flomfy_prep": [w, h, n, ow, oh, frames]}
        return {"ui": ui, "result": (out, mask, info, w, h, ow, oh, n, frames)}


NODE_CLASS_MAPPINGS = {
    "FlomfyImagePrepper": ImagePrepper,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "FlomfyImagePrepper": "Flomfy Image Prepper (frames + letterbox)",
}
