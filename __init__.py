"""ComfyUI-Flomfy-Nodes: helper nodes shipped with Flomfy (OCIO info parsing, frame padding)."""

from .flomfy import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

# Frontend extension (shows sizes on the Letterbox node after it runs).
WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
