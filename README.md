# ComfyUI-Flomfy-Nodes

Helper nodes shipped with Flomfy.

## Install

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/OWNER/ComfyUI-Flomfy-Nodes
```

No extra dependencies (uses the torch that ComfyUI already has). Restart ComfyUI.

## Nodes

### Flomfy OCIO Info Parse (`FlomfyOCIOInfoParse`, `utils/ocio`)
Parses the OCIORead `info` string into `frame_count`, `first_frame`, `last_frame`,
`width`, `height`.

### Flomfy LTX Stage1 Helper (`FlomfyLTXStage1Helper`, `utils/ltx`)
Downscales an IMAGE batch to the LTX stage-1 size: the input size divided by
`downscale_multiplier`, each side snapped to a multiple of 32 (`resize_method`: area,
bicubic, bilinear, nearest-exact). Outputs the resized `image`, `stage1_width`,
`stage1_height` and `downscale_multiplier`.

### Flomfy Frame Padder (hold last) (`FlomfyFramePadder`, `utils/ocio`)
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
