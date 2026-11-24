"""Flomfy node modules.

To add nodes: create a module in this folder with NODE_CLASS_MAPPINGS (and
optionally NODE_DISPLAY_NAME_MAPPINGS), then add it to MODULES below.
Node IDs are prefixed "Flomfy" and must never be renamed: saved workflows use them.
"""

from . import frames, letterbox, ltx, ocio

MODULES = [ocio, frames, ltx, letterbox]

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}
for _module in MODULES:
    for _key, _cls in _module.NODE_CLASS_MAPPINGS.items():
        if _key in NODE_CLASS_MAPPINGS:
            raise RuntimeError(f"Duplicate Flomfy node id: {_key}")
        NODE_CLASS_MAPPINGS[_key] = _cls
    NODE_DISPLAY_NAME_MAPPINGS.update(getattr(_module, "NODE_DISPLAY_NAME_MAPPINGS", {}))
