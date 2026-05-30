import argparse
import sys
import cv2
import numpy as np
from pathlib import Path

from olat_relight.olat_relight import OLATRelightWithEnvMap
from utils.metadata_readers import read_OLAT_info


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render a 360° rotation relighting video for a single subject.")
    # Identity
    parser.add_argument("--subjectID",  type=str, required=True, help="Subject ID, e.g. data-040325-C014")
    parser.add_argument("--envmap_id",  type=str, default="street", help="Environment map ID, e.g. street, courtyard, studio")
    # Paths
    parser.add_argument("--olat_path",    type=str, required=True, help="Root path of the OLAT upload folder")
    parser.add_argument("--shared_path", type=str, required=False, default = "../" ,help="hardcode path of shared folder")
    parser.add_argument("--envmap_dir",   type=str, default="./olat_relight/example_envmaps", help="Directory containing .exr environment maps")
    parser.add_argument("--out_root",     type=str, default="./out_final", help="Root output directory")
    # Camera & rendering
    parser.add_argument("--cam",        type=str, default="Cam06", help="relit which cameras")
    parser.add_argument("--tgt_w",      type=int, default=750,  help="Target image width for loading/downsampling")
    parser.add_argument("--num_frames", type=int, default=100,  help="Number of rotation frames")
    parser.add_argument("--fps",        type=int, default=24,   help="Output video FPS")
    parser.add_argument("--margin",     type=int, default=100,  help="Pixel margin around the mask bounding box")
    parser.add_argument("--out_size",   type=int, default=512,  help="Output frame size (square)")
    parser.add_argument("--scale",   type=float, default=0.5,  help="scale OLAT basis for merging")
    return parser.parse_args()


def load_mask(mask_path: Path, tgt_w: int) -> np.ndarray:
    """Load mask image, downsample if needed, and return as 3-channel float32 [0, 1]."""
    raw = cv2.imread(str(mask_path), cv2.IMREAD_UNCHANGED)
    if raw is None:
        sys.exit(f"Mask not found: {mask_path}")

    mask = np.float32(raw) / 255.0
    h, w = mask.shape[:2]
    if w != tgt_w:
        scale = w / tgt_w
        mask = cv2.resize(mask, (int(w / scale), int(h / scale)), interpolation=cv2.INTER_AREA)

    if mask.ndim == 2:
        mask = np.dstack([mask] * 3)
    elif mask.shape[2] == 4:
        mask = mask[..., :3]

    return mask


def compute_crop_box(mask: np.ndarray, margin: int) -> tuple[int, int, int, int]:
    """Return a square (x0, y0, x1, y1) crop box centred on the foreground."""
    alpha = mask[..., 0]
    ys, xs = np.where(alpha > 0)
    if len(xs) == 0:
        sys.exit("Mask is entirely empty — cannot compute crop box.")

    h, w = alpha.shape
    x_min = max(0, xs.min() - margin)
    x_max = min(w, xs.max() + margin)
    y_min = max(0, ys.min() - margin)
    y_max = min(h, ys.max() + margin)

    side = max(x_max - x_min, y_max - y_min)
    cx, cy = (x_min + x_max) // 2, (y_min + y_max) // 2
    half = side // 2

    x0 = max(0, cx - half)
    y0 = max(0, cy - half)
    x1 = min(w, cx + half)
    y1 = min(h, cy + half)
    return x0, y0, x1, y1


def main() -> None:
    args = parse_args()

    olat_path    = Path(args.olat_path)
    shared_path = Path(args.shared_path)
    envmap_dir   = Path(args.envmap_dir)
    postfix      = str(args.scale)
    out_path     = Path(args.out_root) / f"relight_{postfix}" / args.subjectID / args.envmap_id
    out_path.mkdir(parents=True, exist_ok=True)

    print(f"Subject  : {args.subjectID}")
    print(f"Envmap   : {args.envmap_id}")
    print(f"Scale OLAT  : {args.scale}")
    print(f"Output   : {out_path}")

    # --- Metadata ------------------------------------------------------------
    lights_pos_path  = shared_path / "shared" / "LSX_light_positions_aligned.pc"
    lights_sort_path = shared_path / "shared" / "LSX3_light_z_spiral.txt"
    olat_envmaps_path = shared_path / "shared" / "envmap_zspiral_mpi"
    light_positions, light_img = read_OLAT_info(
        lights_pos_path, lights_sort_path,
        OLAT_START=14, OLAT_FB_MODULO=21, exclude_door_lights=False,
    )

    # --- Relighter -----------------------------------------------------------
    print("Building OLAT relighter ...")
    olat_relighter = OLATRelightWithEnvMap(olat_envmaps_path)

    # --- Mask ----------------------------------------------------------------
    print("Loading mask ...")
    mask = load_mask(olat_path / args.subjectID / "mask" / f"{args.cam}.png", args.tgt_w)
    print(f"  Mask shape : {mask.shape}")

    crop_box = compute_crop_box(mask, args.margin)
    print(f"  Crop box   : {crop_box}")

    # --- OLATs ---------------------------------------------------------------
    print("Loading OLATs ...")
    olat_dir = olat_path / args.subjectID / "masked_olat" / args.cam
    olat_paths = sorted(olat_dir.glob("*.avif"))
    if not olat_paths:
        sys.exit(f"No .avif files found in {olat_dir}")

    olat_relighter.load_olats(args.subjectID, [olat_paths[i] for i in light_img], tgt_w=args.tgt_w, scale=args.scale)

    # --- Environment map -----------------------------------------------------
    print("Loading environment map ...")
    envmap_file = envmap_dir / f"{args.envmap_id}.exr"
    if not envmap_file.exists():
        sys.exit(f"Environment map not found: {envmap_file}")

    olat_relighter.load_envmap(args.envmap_id, str(envmap_file), scale_to_0_1=False)

    # --- Video writer --------------------------------------------------------
    out_size   = (args.out_size, args.out_size)
    video_path = out_path / f"{args.subjectID}_{args.envmap_id}_rotation.mp4"
    fourcc     = cv2.VideoWriter_fourcc(*"mp4v")
    writer     = cv2.VideoWriter(str(video_path), fourcc, args.fps, out_size)

    # --- Render frames -------------------------------------------------------
    step_deg = 360.0 / args.num_frames
    x0, y0, x1, y1 = crop_box

    for frame_idx in range(args.num_frames):
        yaw_deg = frame_idx * step_deg
        yaw_rad = np.deg2rad(yaw_deg)
        print(f"  Frame {frame_idx:3d}/{args.num_frames}  yaw={yaw_deg:6.2f}°")

        relit = olat_relighter.relight_rot(args.subjectID, args.envmap_id, yaw=yaw_rad, scale=1.0)

        frame = (np.clip(relit, 0.0, 1.0) * mask * 255).astype(np.uint8)
        frame = cv2.resize(frame[y0:y1, x0:x1], out_size, interpolation=cv2.INTER_AREA)

        cv2.imwrite(str(out_path / f"{args.subjectID}_{args.envmap_id}_yaw{int(yaw_deg):03d}.png"), frame)
        writer.write(frame)

    writer.release()
    print(f"\nDone. {args.num_frames} frames saved to {out_path}")
    print(f"Video : {video_path}")


if __name__ == "__main__":
    main()