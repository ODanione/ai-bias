# Agent Instructions

This file explains how an AI coding agent should work in this repository.

## Purpose

This project studies visible bias patterns in image generation by comparing image sets across sources and categories.

There are two public homes for the project:

- GitHub code repo: `https://github.com/ODanione/ai-bias`
- Hugging Face dataset repo: `https://huggingface.co/datasets/ODanione/ai-bias-images`

Treat GitHub as the source of truth for code and lightweight metadata.
Treat Hugging Face as the source of truth for the large AI-generated image corpus.

## Public data policy

Only the AI-generated image folders are intended for the public dataset:

- `FLUX/`
- `FLUX2/`
- `NanoBanana/`
- `Sora/`

Do not publish these folders to GitHub unless the user explicitly changes the repository strategy.

Do not publish these folders as part of the public dataset:

- `AdobeStock/`
- `GoogleSearch/`
- `Papers/`
- `_Obsolete/`

Reason:

- `AdobeStock/` and `GoogleSearch/` contain third-party reference material.
- `Papers/` contains papers and reference documents.
- `_Obsolete/` is intentionally local-only historical material.

## Local filesystem expectations

This repo may contain large local directories that are not tracked on GitHub.
If a script or task needs the AI-generated corpus and the directories are missing locally, fetch them from the Hugging Face dataset repo instead of assuming Git history contains them.

The scripts currently assume the existing local folder structure, especially under:

- `FLUX/`
- `FLUX2/`
- `NanoBanana/`
- `Sora/`

Do not change those script assumptions casually. If a folder layout is changed, update the scripts and the documentation in the same task.

## Secrets

Secrets are local-only.

Expected local secret variables:

- `OPENAI_API_KEY`
- `HF_TOKEN`

Rules:

- Never commit `.env`
- Never print tokens into committed files
- Never add credentials to README, scripts, or dataset cards
- If a token is exposed in chat or logs, recommend rotation

## Git and publishing rules

GitHub should contain:

- scripts
- prompts
- schema files
- small derived metadata such as `statistics.json`
- documentation

GitHub should not contain:

- large image corpora
- local virtualenv contents
- local secrets
- third-party reference image sets

Hugging Face dataset publishing should:

- use dataset repo `ODanione/ai-bias-images`
- keep license metadata aligned with the current project decision
- preserve the folder structure unless the user asks for a migration
- exclude `_Obsolete/`, `AdobeStock/`, `GoogleSearch/`, and `Papers/`

## Documentation expectations

When changing project structure, publishing rules, or secret handling, update:

- `README.md`
- this `AGENTS.md` file if the workflow expectations for agents changed

Keep the documentation consistent with the actual storage split between GitHub and Hugging Face.

## Recommended workflow for future agents

1. Check whether the task affects code, local-only data, or the public dataset.
2. Avoid touching secrets except to read them from local environment or `.env`.
3. If changing image layout or dataset contents, verify whether scripts need corresponding updates.
4. If publishing data, keep third-party and obsolete folders excluded.
5. If publishing code, keep the GitHub repo lightweight and avoid reintroducing large image folders into Git history.
