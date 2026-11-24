# ComfyUI-Flomfy-Nodes

Helper nodes shipped with Flomfy.

## Install

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/OWNER/ComfyUI-Flomfy-Nodes
```

No extra dependencies (uses the torch that ComfyUI already has). Restart ComfyUI.

## Nodes (category `utils/ocio`)

### Flomfy OCIO Info Parse (`FlomfyOCIOInfoParse`)
Parses the OCIORead `info` string into `frame_count`, `first_frame`, `last_frame`,
`width`, `height`, plus `stage1_width` / `stage1_height`: the plate size divided by
`upscale_factor` and snapped to a multiple of 32.

### Flomfy Frame Padder (hold last) (`FlomfyFramePadder`)
Fits an IMAGE batch to a length of the form `a*n+b` (`8n+1` for LTX, `4n+1` for Wan, ...).
- `hold_pad`: repeat the last frame up to the next valid length.
- `trim`: cut down to the previous valid length (pads instead if the clip is too short).
- `original`: pass through.

Outputs `images`, `length`, `original_length`, `pad_frames` (negative when trimmed).

## Adding nodes

Put a module in `flomfy/` with `NODE_CLASS_MAPPINGS` / `NODE_DISPLAY_NAME_MAPPINGS`,
add it to `MODULES` in `flomfy/__init__.py`, and add tests in `tests/`.
Node IDs start with `Flomfy` and must not be renamed once released (saved workflows use them).

## Tests

```bash
python -m pytest tests
```
