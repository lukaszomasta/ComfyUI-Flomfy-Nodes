"""LTX helper nodes."""

import torch.nn.functional as F

from ._common import CATEGORY_LTX, snap

# LTX latents need width and height divisible by 32.
STAGE1_MULTIPLE = 32
RESIZE_METHODS = ["area", "bicubic", "bilinear", "nearest-exact"]


def stage1_size(width, height, downscale_multiplier):
    """Plate size divided by downscale_multiplier, each side snapped to a multiple of 32."""
    return (snap(width / downscale_multiplier, STAGE1_MULTIPLE),
            snap(height / downscale_multiplier, STAGE1_MULTIPLE))


def resize(images, width, height, method):
    """Resize an IMAGE batch (B, H, W, C) to (B, height, width, C)."""
    if images.shape[1] == height and images.shape[2] == width:
        return images
    x = images.movedim(-1, 1)
    if method in ("bilinear", "bicubic"):
        x = F.interpolate(x, size=(height, width), mode=method, align_corners=False, antialias=True)
    else:
        x = F.interpolate(x, size=(height, width), mode=method)
    return x.movedim(1, -1).clamp(0.0, 1.0)


class LTXStage1Helper:
    """Downscale an IMAGE batch to the LTX stage-1 size: plate / downscale_multiplier,
    each side snapped to a multiple of 32."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "downscale_multiplier": ("INT", {"default": 2, "min": 1, "max": 4}),
                "resize_method": (RESIZE_METHODS, {"default": "area"}),
            }
        }

    RETURN_TYPES = ("IMAGE", "INT", "INT", "INT")
    RETURN_NAMES = ("image", "stage1_width", "stage1_height", "downscale_multiplier")
    FUNCTION = "run"
    CATEGORY = CATEGORY_LTX

    def run(self, image, downscale_multiplier, resize_method):
        height, width = image.shape[1], image.shape[2]
        s1w, s1h = stage1_size(width, height, downscale_multiplier)
        return (resize(image, s1w, s1h, resize_method), s1w, s1h, downscale_multiplier)


NODE_CLASS_MAPPINGS = {
    "FlomfyLTXStage1Helper": LTXStage1Helper,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "FlomfyLTXStage1Helper": "Flomfy LTX Stage1 Helper",
}
