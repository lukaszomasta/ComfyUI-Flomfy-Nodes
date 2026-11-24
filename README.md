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
Computes the LTX stage-1 size from an IMAGE batch: the input size divided by
`downscale_multiplier`, each side snapped to a multiple of 32. Outputs the `image`
unchanged (not resized), `stage1_width`, `stage1_height` and `downscale_multiplier`.

### Flomfy Frame Padder (hold last) (`FlomfyFramePadder`, `utils/ocio`)
Fits an IMAGE batch to the frame count a video model expects. `formula` is a dropdown:

| Preset | Rule |
|---|---|
| LTX / LTX-2, Cosmos 1 | `8n+1` |
| Wan 2.1 / 2.2, HunyuanVideo, Kandinsky 5, Cosmos Predict2 | `4n+1` |
| Mochi | `6n+1` |
| MiniMax H3 | `17n+5` (5, 22, 39 … 124 ≈ 5 s at 24 fps) |
| custom | `custom_formula`, any `a*n+b` (e.g. `16n`) |

Workflows saved with a typed formula (before the dropdown) keep working.

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
