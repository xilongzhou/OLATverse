import os
import argparse
import subprocess


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", type=str, required=True, help="Environment map ID to relight under")
    parser.add_argument("--olat_path", type=str, required=True, help="Path of OLAT folder")
    parser.add_argument("--obj_list", type=str, nargs="+", required=True, metavar="ID", default='data-040325-C091',
                        help="One or more object IDs, e.g. --obj_list data-040325-C091 data-040325-C014")
    parser.add_argument("--scale_olat", type=float, default=0.5, help="scale up/down OLAT basis(default 0.5): since released OLAT avif is scale by 2 for visualization")
    parser.add_argument("--tgt_w", type=int, default=750, help="Default width for relighting")
    args = parser.parse_args()

    for objID in args.obj_list:
        obj_path = os.path.join(args.olat_path, objID)
        print(f"Processing: {objID}  (path: {obj_path})")

        cmd = [
            "python",
            "relight_single_rot.py",
            "--olat_path", args.olat_path,
            "--subjectID", objID,
            "--envmap_id", args.env,
            "--tgt_w", str(args.tgt_w),  # must be str for subprocess
            "--scale", str(args.scale_olat),  # must be str for subprocess
        ]

        print("Running:", " ".join(cmd))
        subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()