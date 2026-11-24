"""LTX helper nodes."""

from ._common import CATEGORY_LTX, snap

# LTX latents need width and height divisible by 32.
STAGE1_MULTIPLE = 32


def stage1_size(width, height, downscale_multiplier):
    """Plate size divided by downscale_multiplier, each side snapped to a multiple of 32."""
    return (snap(width / downscale_multiplier, STAGE1_MULTIPLE),
            snap(height / downscale_multiplier, STAGE1_MULTIPLE))


class LTXStage1Helper:
    """Pass an IMAGE batch through unchanged and output the LTX stage-1 size:
    image size / downscale_multiplier, each side snapped to a multiple of 32."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "downscale_multiplier": ("INT", {"default": 2, "min": 1, "max": 4}),
            }
        }

    RETURN_TYPES = ("IMAGE", "INT", "INT", "INT")
    RETURN_NAMES = ("image", "stage1_width", "stage1_height", "downscale_multiplier")
    FUNCTION = "run"
    CATEGORY = CATEGORY_LTX

    def run(self, image, downscale_multiplier):
        height, width = image.shape[1], image.shape[2]
        s1w, s1h = stage1_size(width, height, downscale_multiplier)
        return (image, s1w, s1h, downscale_multiplier)


NODE_CLASS_MAPPINGS = {
    "FlomfyLTXStage1Helper": LTXStage1Helper,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "FlomfyLTXStage1Helper": "Flomfy LTX Stage1 Helper",
}
