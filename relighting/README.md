# Relighting Code for OLATverse

Render 360° rotation relighting videos for OLATverse subjects under various environment maps.
This code is based on [HumanOLAT](https://github.com/TMT22/HumanOLAT).

---

## Environment Setup

```bash
conda create --file environment.yml
```

---

## Data Preparation

Download [OLATverse](https://gvv-assets.mpi-inf.mpg.de/OLATverse/) and save it to a directory of your choice, referred to as `$OLAT_PATH` below.

Available environment maps are provided in `olat_relight/example_envmaps/`:
```
olat_relight/example_envmaps/
├── street.exr
├── bedroom.exr
├── class.exr
└── ...
```

---

## Usage

### Relight subjects

```bash
python batch_relit.py \
    --env $ENV_NAME \
    --source_path $OLAT_PATH \
    --obj_list $SUBJECT_IDs
```
For example:
```bash
python batch_relit.py --env street --source_path $OLAT_PATH --obj_list data-040325-C091 data-040325-C014
```


---

## Output

Results are saved to `./out_final/relight_{scale}/$SUBJECT_ID/$ENV_NAME/`, containing per-frame `.png` images and a `.mp4` rotation video.
