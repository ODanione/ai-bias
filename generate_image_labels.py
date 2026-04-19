import argparse
import asyncio
import base64
import json
import mimetypes
import os
import re
import sys
import random
from typing import Any, Dict, Optional, List

from dotenv import load_dotenv
from openai import AsyncOpenAI, RateLimitError

load_dotenv()


API_KEY_ENV_VAR = "OPENAI_API_KEY"
CAPTION_PROMPT_FILE = "Generate_Image_Labels_Prompt.txt"

# Only process these image types
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}


def extract_json_object(text: str) -> Dict[str, Any]:
    """Extract a JSON object from model output."""
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass

    if "```" in text:
        parts = text.split("```")
        for part in parts:
            candidate = part.strip()
            if not candidate:
                continue

            if "\n" in candidate:
                first_line, rest = candidate.split("\n", 1)
                if first_line.strip().lower().startswith("json"):
                    candidate = rest.strip()

            try:
                obj = json.loads(candidate)
                if isinstance(obj, dict):
                    return obj
            except json.JSONDecodeError:
                continue

    for match in re.finditer(r"\{.*?\}", text, re.DOTALL):
        candidate = match.group(0)
        try:
            obj = json.loads(candidate)
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            continue

    raise ValueError("No valid JSON object found in model output")


def normalize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize model output to the repository's current field names."""
    normalized = dict(payload)

    if "perceived_gender" not in normalized and "gender" in normalized:
        normalized["perceived_gender"] = normalized.pop("gender")

    if (
        "perceived_ancestry_cluster" not in normalized
        and "ancestry_cluster" in normalized
    ):
        normalized["perceived_ancestry_cluster"] = normalized.pop("ancestry_cluster")

    return normalized


def read_text_file(path: str, description: str) -> str:
    """Read a text file and exit with a helpful error if not found."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Error: {description} file not found at {os.path.abspath(path)}")
        sys.exit(1)


def read_api_key_from_env() -> str:
    """Read the OpenAI API key from the environment or exit with a clear action."""
    api_key = os.getenv(API_KEY_ENV_VAR, "").strip()
    if api_key:
        return api_key

    print(
        "Error: OPENAI_API_KEY is not set.\n"
        "Set it before running this script.\n"
        "Example:\n"
        "  export OPENAI_API_KEY='your-api-key-here'\n"
        "You can also put OPENAI_API_KEY in your local .env and load it into the environment.\n"
        "Then re-run the script."
    )
    sys.exit(1)


def encode_image_to_data_url(image_path: str) -> Optional[str]:
    """
    Encode an image file as a data: URL (base64) suitable for vision models.

    Returns None if the file is not a supported image.
    """
    mime_type, _ = mimetypes.guess_type(image_path)
    if not mime_type or not mime_type.startswith("image/"):
        print(f"Skipping unsupported file type: {image_path}")
        return None

    try:
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        return f"data:{mime_type};base64,{b64}"
    except Exception as e:
        print(f"Error reading image {image_path}: {e}")
        return None


async def generate_caption_for_image(
    client: AsyncOpenAI,
    image_path: str,
    caption_prompt: str,
    model: str = "gpt-4o",
    detail: str = "high",
    stream: bool = True,
    max_retries: int = 5,
) -> Optional[str]:
    """
    Call the OpenAI API with a text prompt + image and return the generated caption.

    Uses streaming under the hood (stream=True) and assembles the full text.
    """
    data_url = encode_image_to_data_url(image_path)
    if data_url is None:
        return None

    # System prompt replaces your old assistant instructions
    system_prompt = (
        "You extract structured visual attributes from an input image. "
        "Use only visible presentation in the image, not identity claims or hidden traits. "
        "For sensitive attributes, provide perceived categories based on appearance only. "
        "Use 'unknown' only when the image is too ambiguous, obscured, or low-quality to make a reasonable visual estimate. "
        "Return exactly one valid JSON object and no surrounding prose, markdown, or code fences."
    )

    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": caption_prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": data_url,
                        "detail": detail,
                    },
                },
            ],
        },
    ]

    for attempt in range(max_retries + 1):
        try:
            # --- Streaming version ---
            if stream:
                chunks: List[str] = []

                response_stream = await client.chat.completions.create(
                    model=model,
                    messages=messages,
                    response_format={"type": "json_object"},
                    stream=True,
                )

                # We assemble the full text; if you want to print token-by-token,
                # you can also print inside this loop.
                async for chunk in response_stream:
                    choice = chunk.choices[0]
                    delta = choice.delta

                    # delta.content is typically a string for text tokens
                    if delta and delta.content:
                        chunks.append(delta.content)

                full_text = "".join(chunks).strip()
                return full_text or None

            # --- Non-streaming fallback (unused currently, but handy to keep) ---
            completion = await client.chat.completions.create(
                model=model,
                messages=messages,
                response_format={"type": "json_object"},
                stream=False,
            )
            content = completion.choices[0].message.content
            return content.strip() if content else None
        except RateLimitError as exc:
            if attempt >= max_retries:
                raise

            delay_seconds = min(2**attempt, 10) + random.uniform(0, 1)
            print(
                f"⚠️  Rate limit for {image_path}. "
                f"Retrying in {delay_seconds:.1f}s ({attempt + 1}/{max_retries})"
            )
            await asyncio.sleep(delay_seconds)

            continue


async def process_single_image(
    client: AsyncOpenAI,
    image_path: str,
    caption_prompt: str,
    semaphore: asyncio.Semaphore,
    model: str,
    detail: str,
) -> None:
    """
    Process one image:
    - send it to the model
    - get the JSON label
    - write JSON to a .json file next to the image
    """
    async with semaphore:
        print(f"→ Processing: {image_path}")
        caption = await generate_caption_for_image(
            client,
            image_path,
            caption_prompt,
            model=model,
            detail=detail,
        )

        if not caption:
            print(f"⚠️  No caption generated for {image_path}")
            return

        try:
            payload = normalize_payload(extract_json_object(caption))
            payload["eval_model"] = model
        except ValueError as e:
            print(f"⚠️  Could not parse JSON for {image_path}: {e}")
            return

        output_path = os.path.splitext(image_path)[0] + ".json"
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
                f.write("\n")
            print(f"✅ JSON saved to: {output_path}")
        except Exception as e:
            print(f"Error writing JSON for {image_path}: {e}")


async def process_directory(
    directory: str,
    max_concurrency: int = 5,
    model: str = "gpt-4o",
    detail: str = "high",
    overwrite: bool = False,
) -> None:
    """
    Find all images in the directory and process them concurrently
    using an async OpenAI client and a bounded semaphore.
    """
    api_key = read_api_key_from_env()
    caption_prompt = read_text_file(CAPTION_PROMPT_FILE, "Caption prompt")

    client = AsyncOpenAI(api_key=api_key)

    # Collect all image paths
    image_paths: List[str] = []
    for name in os.listdir(directory):
        full_path = os.path.join(directory, name)
        if not os.path.isfile(full_path):
            continue

        ext = os.path.splitext(name)[1].lower()
        if ext in IMAGE_EXTENSIONS:
            output_path = os.path.splitext(full_path)[0] + ".json"
            if not overwrite and os.path.exists(output_path):
                continue
            image_paths.append(full_path)

    if not image_paths:
        print(f"No images with extensions {sorted(IMAGE_EXTENSIONS)} found in {directory}")
        return

    print(f"Found {len(image_paths)} image(s) in {directory}")
    print(f"Using model: {model}")
    print(f"Using detail: {detail}")
    print(f"Max concurrency: {max_concurrency}")

    semaphore = asyncio.Semaphore(max_concurrency)

    tasks = [
        process_single_image(client, img_path, caption_prompt, semaphore, model, detail)
        for img_path in image_paths
    ]

    await asyncio.gather(*tasks)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate JSON labels for images in a directory."
    )
    parser.add_argument("directory", help="Directory containing image files")
    parser.add_argument(
        "--model",
        default="gpt-4o",
        help="OpenAI model to use for image categorization (default: gpt-4o)",
    )
    parser.add_argument(
        "--detail",
        choices=["low", "high", "auto"],
        default="high",
        help="Image detail level to send to the model (default: high)",
    )
    parser.add_argument(
        "--max-concurrency",
        type=int,
        default=5,
        help="Number of concurrent OpenAI requests (default: 5)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Regenerate labels even if a sidecar .json already exists",
    )
    args = parser.parse_args()

    directory = args.directory

    if not os.path.isdir(directory):
        print(f"Error: {directory} is not a valid directory")
        sys.exit(1)

    asyncio.run(
        process_directory(
            directory,
            max_concurrency=args.max_concurrency,
            model=args.model,
            detail=args.detail,
            overwrite=args.overwrite,
        )
    )


if __name__ == "__main__":
    main()
