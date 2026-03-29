# AI Image Bias Mini-Study

This repository contains a small exploratory study on bias in AI image generation. The basic idea is simple: compare how different image sources represent the same role or person label, then inspect recurring patterns in gender, perceived ancestry, skin tone, age, and other visible traits.

This is not a formal benchmark or a publication-ready dataset. It is a personal research project intended to make patterns visible quickly.

## What is in the repo

The repository mixes image collections, labeling helpers, and lightweight analysis tooling.

- `AdobeStock/`, `GoogleSearch/`: quick reference samples used as a rough check of what bias looks like in internet-visible imagery, based on the first 24 images found per category.
- `FLUX/`, `FLUX2/`, `Sora/`, `NanoBanana/`: AI-generated image sets grouped by prompt target such as `CEO`, `Cashier`, `Doctor`, `Teacher`, or `Person`.
- `Papers/`: background reading related to the topic.
- `statistics.json`: the currently aggregated structured labels used by the explorer UI.
- `charactgeristics.json`: a JSON schema draft for the person-attribute labels.
- `Categorize_Prompt.txt`: the prompt used to ask a vision model to extract structured attributes from images.
- `categorize.py`: generates one JSON-like `.txt` label file per image using the OpenAI API.
- `statistics_generate.py`: collects those `.txt` files into `statistics.json`.
- `statistics_show.py`: starts a local Flask app for interactively exploring the aggregated labels.
- `rasterize.py`: creates a contact-sheet style composite image from a directory of images.

## Corpus shape

The image corpus currently contains 1,422 image files across the main source folders:

- `AdobeStock`: 240 images
- `FLUX`: 250 images
- `FLUX2`: 320 images
- `GoogleSearch`: 252 images
- `NanoBanana`: 132 images
- `Sora`: 228 images

Most folders are organized as `SOURCE/CATEGORY/...`, where category names include:

- `CEO`
- `Cashier`
- `Child`
- `Doctor`
- `Engineer`
- `Housekeeper`
- `Person`
- `Prisoner`
- `Social Worker`
- `Teacher`

There are also a few extra or incomplete branches, such as `Sora/Police Car` and `_Obsolete/`.

For `GoogleSearch` and `AdobeStock`, the intent was not to build a carefully curated benchmark. They were meant as a short sanity check for "bias on the internet in general": for each category, the first 24 images found in Google Image Search or Adobe Stock were saved.

## Current labeled subset

The current `statistics.json` does not describe the whole corpus. It contains 48 labeled samples only, and all of them come from the `FLUX` directory:

- 24 `CEO` images
- 24 `Cashier` images

Those labels were generated from the `.txt` sidecar files in:

- `FLUX/CEO`
- `FLUX/Cashier`

The extracted attributes currently include:

- `gender`
- `age_estimate`
- `ancestry_cluster`
- `skin_tone`
- `eye_color`
- `hair_color`
- `glasses`
- `beard_style`

Within this small labeled subset, the strongest visible pattern is exactly the kind of occupational stereotyping this repo appears to investigate:

- `Cashier` is labeled almost entirely as female.
- `CEO` is labeled almost entirely as male.
- Both groups skew heavily toward light skin tones.
- `CEO` skews strongly `West Eurasian` in the current labels.

That is not enough to make a strong statistical claim about all generators in the repo, but it is enough to show why the broader corpus is interesting.

## Workflow

The workflow in this repo appears to be:

1. Collect or generate images for the same prompt category from different sources.
2. Use `categorize.py` with `Categorize_Prompt.txt` to extract structured person attributes from each image.
3. Save one `.txt` result next to each image.
4. Run `statistics_generate.py` to combine those outputs into `statistics.json`.
5. Explore the results in `statistics_show.py` or build visual sheets with `rasterize.py`.

## Scripts

### Categorize images

`categorize.py` sends images to the OpenAI API and writes a `.txt` file next to each image containing the extracted JSON fields.

Prerequisites:

- Python 3
- `openai`
- `OPENAI_API_KEY` set in your environment

Run:

```bash
export OPENAI_API_KEY="your-api-key-here"
python categorize.py FLUX/Cashier
```

Notes:

- The script reads the prompt from `Categorize_Prompt.txt`.
- It currently processes `.png`, `.jpg`, and `.jpeg` files.
- `categorizeV1.py` is an older version based on the Assistants API.
- A local `.env` file is also fine if you load it into the environment and keep it out of Git.

### Build `statistics.json`

This script walks one directory level below the given base directory, reads `.txt` files, extracts JSON objects, and appends the folder name as `person_type`.

```bash
python statistics_generate.py FLUX
```

That writes `statistics.json` into the current working directory.

### Explore the labels in a browser

Install Flask and start the local explorer:

```bash
pip install flask
python statistics_show.py
```

Then open `http://127.0.0.1:5000/`.

The UI lets you filter the current `statistics.json` and inspect per-attribute distributions.

This replaces the older note from `readme.txt`, which referred to the same local statistics webpage.

### Create contact sheets

`rasterize.py` builds a fixed-size image grid from all images in a directory.

Example:

```bash
python rasterize.py 6 4 2400 1600 FLUX/Cashier --output cashier_grid.jpg
```

## Interpretation and limitations

This repo is useful for exploratory inspection, but it has important limitations:

- The prompts and category names are socially loaded and likely drive stereotype-heavy outputs.
- The attribute extraction is itself model-based, so the labels can encode another layer of bias.
- The current aggregated analysis covers only a small subset of the available images.
- The `GoogleSearch` and `AdobeStock` sets are convenience samples from the first results found, not controlled or representative internet measurements.
- Several categories are not present in every source.
- Image counts are not perfectly uniform across all folders.

Because of that, this project is best read as an exploratory artifact: a way to surface patterns, not a definitive measurement of bias.

## Possible next steps

- Generate `.txt` labels for the rest of the corpus.
- Build one `statistics.json` per source and compare them side by side.
- Keep prompt wording constant and document it explicitly for each source.
- Add simple plots or exported CSV summaries.
- Add a short methodology note for how reference images were collected.
