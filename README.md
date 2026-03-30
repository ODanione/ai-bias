# AI Image Bias Mini-Study

This repository contains a small exploratory study on bias in AI image generation. The basic idea is simple: compare how different image sources represent the same role or person label, then inspect recurring patterns in perceived gender, perceived ancestry, skin tone, age, and other visible traits.

This is not a formal benchmark or a publication-ready dataset. It is a personal research project intended to make patterns visible quickly.

## Repository layout

This project is intentionally split across two remotes:

- Code and lightweight metadata live on GitHub: `https://github.com/ODanione/ai-bias`
- The AI-generated image corpus lives on Hugging Face: `https://huggingface.co/datasets/ODanione/ai-bias-images`

The GitHub repository is the canonical home for scripts, prompts, schema drafts, and small derived artifacts such as `statistics.json`.
The Hugging Face dataset is the canonical home for the large AI-generated image folders.

## What is in the repo

The repository mixes image collections, labeling helpers, and lightweight analysis tooling.

- `AdobeStock/`, `GoogleSearch/`: quick reference samples used as a rough check of what bias looks like in internet-visible imagery, based on the first 24 images found per category.
- `FLUX/`, `FLUX2/`, `Sora/`, `NanoBanana/`, `Qwen/`: AI-generated image sets grouped by prompt target such as `CEO`, `Cashier`, `Doctor`, `Teacher`, or `Person`.
- `Papers/`: background reading related to the topic.
- `statistics.json`: the currently aggregated structured labels used by the explorer UI.
- `charactgeristics.json`: a JSON schema draft for the person-attribute labels.
- `Generate_Image_Labels_Prompt.txt`: the prompt used to ask a vision model to extract structured attributes from images.
- `generate_image_labels.py`: generates one `.json` label file per image using the OpenAI API.
- `statistics_generate.py`: collects those `.json` files into `statistics.json`.
- `statistics_show.py`: starts a local Flask app for interactively exploring the aggregated labels.
- `rasterize.py`: creates a contact-sheet style composite image from a directory of images.

## Storage policy

The project contains three different classes of assets:

- Code and small metadata files: kept in GitHub
- AI-generated image corpora that the project controls: published on Hugging Face
- Third-party or local-only material: kept out of public dataset hosting

Current policy:

- Public on Hugging Face:
  - `FLUX/`
  - `FLUX2/`
  - `NanoBanana/`
  - `Qwen/`
  - `Sora/`
- Not published as part of the public dataset:
  - `AdobeStock/`
  - `GoogleSearch/`
  - `Papers/`
  - `_Obsolete/`
  - local secrets and local virtual environments

This split exists because the public dataset is limited to AI-generated images that are under project control, while third-party and reference material remain local-only.

## Corpus shape

The image corpus currently contains 1,392 image files across the main source folders:

- `AdobeStock`: 240 images
- `FLUX`: 250 images
- `FLUX2`: 320 images
- `GoogleSearch`: 186 images
- `NanoBanana`: 72 images
- `Qwen`: 96 images
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

For `GoogleSearch` and `AdobeStock`, the intent was not to build a carefully curated benchmark. They were meant as a short sanity check for "bias on the internet in general": for each category, the first 24 images found in Google Image Search or Adobe Stock were saved.

## Image sources

The image folders mix AI-generated sources and search-based reference sources. The purpose of keeping them separate is to compare how the same role labels are visually represented across generators and across rough internet-facing reference material.

### AI-generated sources

- `FLUX/`: images generated with quantized local runs of Black Forest Labs' `FLUX.1 [dev]` model. Black Forest Labs announced FLUX.1 on August 1, 2024. The broader FLUX.1 line mixes open-weight and closed offerings, but this project's `FLUX/` folder specifically comes from quantized `FLUX.1 [dev]`, the open-weight non-commercial variant.
- `FLUX2/`: images generated with quantized local runs of Black Forest Labs' `FLUX.2 [dev]` model, i.e. the second-generation FLUX line rather than another FLUX.1 run. Black Forest Labs announced FLUX.2 on November 25, 2025. The broader FLUX.2 line mixes API products and open-weight releases, but this project's `FLUX2/` folder specifically refers to quantized `FLUX.2 [dev]` outputs.
- `NanoBanana/`: images generated with Google's Gemini 2.5 Flash Image family. Google introduced Gemini 2.5 Flash Image on August 26, 2025 and explicitly described it as "aka nano-banana". This is a closed Google model delivered through the Gemini API, Google AI Studio, and Vertex AI rather than open weights.
- `Qwen/`: images generated with Qwen-Image from Alibaba's Qwen team. Qwen announced Qwen-Image on August 4, 2025 as a 20B image foundation model and released weights publicly on Hugging Face and ModelScope. In practice this makes `Qwen/` the open-weight image-generator bucket in this repo.
- `Sora/`: images generated with OpenAI Sora. OpenAI first published Sora research on February 15, 2024 and launched Sora as a product for ChatGPT users on December 9, 2024. Sora is a closed OpenAI model and service rather than an open-weight release.

These folders represent model-controlled outputs rather than third-party reference imagery, which is why they are the folders intended for publication in the Hugging Face dataset repo.

License note for AI-generated folders: project metadata and documentation can be published under `CC-BY 4.0`, but the generated images themselves may also remain subject to the license terms, usage policies, or service terms of their upstream model providers. In other words, the dataset should not imply that `CC-BY 4.0` is the only governing layer for `FLUX/`, `FLUX2/`, `NanoBanana/`, `Qwen/`, or `Sora/`.

### Search-based reference sources

- `GoogleSearch/`: images collected from Google Image Search.
- `AdobeStock/`: images collected from Adobe Stock search results.

For both search-based sources, the collection rule was intentionally simple: use the search function for each target label and keep the first 24 sensible results. Obviously irrelevant results were skipped, for example comic or cartoon images, non-person results, or images that clearly did not match the intended query.

These folders are rough reference samples only. They are not controlled datasets and are not published as part of the public Hugging Face dataset.

## Current labeled subset

The current `statistics.json` does not describe the whole corpus. It contains 48 labeled samples only, and all of them come from the `FLUX` directory:

- 24 `CEO` images
- 24 `Cashier` images

Those labels were generated from the sidecar label files in:

- `FLUX/CEO`
- `FLUX/Cashier`

The extracted attributes currently include:

- `perceived_gender`
- `age_estimate`
- `perceived_ancestry_cluster`
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
2. Use `generate_image_labels.py` with `Generate_Image_Labels_Prompt.txt` to extract structured person attributes from each image.
3. Save one `.json` result next to each image.
4. Run `statistics_generate.py` to combine those outputs into `statistics.json`.
5. Explore the results in `statistics_show.py` or build visual sheets with `rasterize.py`.

If you need the full AI-generated corpus and it is not present locally, fetch it from the Hugging Face dataset repo instead of expecting it to exist in GitHub history.

## Scripts

### Categorize images

`generate_image_labels.py` sends images to the OpenAI API and writes a `.json` file next to each image containing the extracted JSON fields.

Prerequisites:

- Python 3
- `openai`
- `OPENAI_API_KEY` set in your environment

Run:

```bash
export OPENAI_API_KEY="your-api-key-here"
python generate_image_labels.py FLUX/Cashier
```

Notes:

- The script reads the prompt from `Generate_Image_Labels_Prompt.txt`.
- It currently processes `.png`, `.jpg`, and `.jpeg` files.
- `categorizeV1.py` is an older version based on the Assistants API.
- A local `.env` file is also fine if you load it into the environment and keep it out of Git.
- The scripts operate on local folders. If the large image directories are missing locally, retrieve them from the Hugging Face dataset first.

### Build `statistics.json`

This script walks one directory level below the given base directory, reads `.json` files, extracts JSON objects, and appends the folder name as `person_type`.

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

## Secrets and local setup

- Keep secrets in a local `.env` file or in exported environment variables.
- Do not commit `.env`, API keys, tokens, or virtual environment contents.
- The local `.venv/` directory is for local execution only and is intentionally ignored by Git.

Typical local secret keys used in this project:

- `OPENAI_API_KEY`
- `HF_TOKEN`

## Possible next steps

- Generate `.json` labels for the rest of the corpus.
- Build one `statistics.json` per source and compare them side by side.
- Keep prompt wording constant and document it explicitly for each source.
- Add simple plots or exported CSV summaries.
- Add a short methodology note for how reference images were collected.
