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

### Flomfy Image Prepper (frames + letterbox) (`FlomfyImagePrepper`, `utils/video`)
Frame Padder and Letterbox in one node: fits the frame count (`frame_rule`, `length_mode`)
and pads the size (`size_rule`, `pad_color`, `position`) with one copy of the frames instead
of two. Same presets as the two nodes below. Outputs `image`, `bars_mask`, `letterbox_info`
(for Flomfy Remove Letterbox), `original_width`, `original_height`, `width`, `height`,
`original_length`, `length`. After a run the node shows the sizes on its outputs
(e.g. `image 1920×1080×100f → 1920×1088×105f`).

### Flomfy Letterbox (pad to size rule) (`FlomfyLetterbox`, `utils/video`)
Pads an IMAGE batch with bars (no scaling) so width and height are multiples of the
target model's size rule:

| Preset | Multiple |
|---|---|
| LTX / LTX-2 two-stage (default) | 64, so stage 1 at half size is still a multiple of 32 |
| LTX / LTX-2, MiniMax H3 | 32 |
| Wan 2.1 / 2.2, HunyuanVideo, Kandinsky 5, Cosmos, Mochi | 16 |
| custom | `custom_multiple` |

`pad_color`: black, gray, white, or edge (repeat the border pixels). `bars_mask` is one
frame shared across the batch, so it costs one frame of memory. `position`: center or
top_left. Outputs the padded `image`, `bars_mask` (1 on the bars), `original_width`,
`original_height`, `width`, `height`, `pad_left`, `pad_top`, and `letterbox_info` for
Flomfy Remove Letterbox. After a run the node shows the sizes on its outputs (e.g. `image 1920×1080 → 1920×1088`).

### Flomfy Remove Letterbox (`FlomfyRemoveLetterbox`, `utils/video`)
Crops the bars back off. Link `letterbox_info` from Flomfy Letterbox. If the image was
resized after padding (stage 1 at half size, an upscaled result), the crop is scaled to
match, e.g. 1920×1080 padded to 1920×1088, rendered at 960×544, crops to 960×540.
Outputs `image`, `width`, `height`.

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
