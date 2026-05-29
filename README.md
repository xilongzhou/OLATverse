# Dataset Structure

This document describes the folder layout and contents of the OLAT dataset splits used for training and validation.

---

## `Tr_Dataset`

Raw training data with background.

| Path | Description |
|------|-------------|
| `olat/` | AVIF images **with** background |
| `mask/` | Mask images (same as `OLATverse_Upload_Tr`) |
| `pbr/` | PBR data (same as `OLATverse_Upload_Tr`) |
| `cameras.calib` / `cameras.xml` | Camera matrix copied from the high-resolution source |
| `all_cam.json` | Low-resolution camera matrix (same as `OLATverse_Upload_Tr`) |

---

## `OLATverse_Upload_Tr`

Final upload of the complete processed **training** dataset.

| Path | Description |
|------|-------------|
| `masked_olat/` | AVIF images **without** background |
| `mask/` | Mask images |
| `pbr/` | PBR data — albedo and normals (see breakdown below) |
| `all_cam.json` | Camera matrix at resolution **1500 × 2844** |

### PBR Sub-folders

| Sub-folder | Description |
|------------|-------------|
| `{CamID}_ncg/` | Normals obtained from color gradient illumination |
| `{CamID}_diff/` | Diffuse albedo derived from 5 polarized views |
| `{CamID}_nd/` | Diffuse normals derived from 5 polarized views |

---

## `OLATverse_Upload_Val`

Final upload of the complete processed **validation** dataset.

| Path | Description |
|------|-------------|
| `masked_olat/` | AVIF images without background (same as Tr) |
| `mask/` | Mask images (same as Tr) |
| `pbr/` | PBR data — albedo and normals (same as Tr) |
| `all_cam.json` | Camera matrix at resolution **1500 × 2844** (same as Tr) |
| `model/` | Reconstructed mesh produced with Metashape |
| `normal_benchmark/` | Normal maps used for benchmarking in the paper |
| `transforms_train.json` / `transforms_test.json` | Transform files used for normal benchmarking in the paper |
