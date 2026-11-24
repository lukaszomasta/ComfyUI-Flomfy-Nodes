"""OCIO helper nodes."""

import re

from ._common import CATEGORY_OCIO


class OCIOInfoParse:
    """Parse the OCIORead `info` string into frame count, frame range and plate size."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "info": ("STRING", {"forceInput": True}),
            }
        }

    RETURN_TYPES = ("INT",) * 5
    RETURN_NAMES = (
        "frame_count",    # 0  original count from the info string
        "first_frame",    # 1
        "last_frame",     # 2
        "width",          # 3  plate width
        "height",         # 4  plate height
    )
    FUNCTION = "parse"
    CATEGORY = CATEGORY_OCIO

    def parse(self, info):
        count = re.search(r"(\d+)\s*frame\(s\)", info)
        rng = re.search(r"frames\s*\[(-?\d+)-(-?\d+)\]", info)
        res = re.search(r"(\d+)x(\d+)", info)

        first = int(rng.group(1)) if rng else 0
        last = int(rng.group(2)) if rng else 0
        n = int(count.group(1)) if count else (last - first + 1 if rng else 0)
        w, h = (int(res.group(1)), int(res.group(2))) if res else (0, 0)

        return (n, first, last, w, h)


NODE_CLASS_MAPPINGS = {
    "FlomfyOCIOInfoParse": OCIOInfoParse,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "FlomfyOCIOInfoParse": "Flomfy OCIO Info Parse",
}
