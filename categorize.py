import asyncio
import base64
import mimetypes
import os
import sys
from typing import Optional, List

from openai import AsyncOpenAI


API_KEY_ENV_VAR = "OPENAI_API_KEY"
CAPTION_PROMPT_FILE = "Categorize_Prompt.txt"

# Only process these image types
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}


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
    model: str = "gpt-5.1",
    stream: bool = True,
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
        "You are an assistant helping to create high-quality prompts for the "
        "AI image generator FLUX, based on the given input image and caption prompt."
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
                        "detail": "low",  # cheaper & sufficient for many captioning tasks
                    },
                },
            ],
        },
    ]

    # --- Streaming version ---
    if stream:
        chunks: List[str] = []

        response_stream = await client.chat.completions.create(
            model=model,
            messages=messages,
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
        stream=False,
    )
    content = completion.choices[0].message.content
    return content.strip() if content else None


async def process_single_image(
    client: AsyncOpenAI,
    image_path: str,
    caption_prompt: str,
    semaphore: asyncio.Semaphore,
) -> None:
    """
    Process one image:
    - send it to the model
    - get the caption
    - write caption to a .txt file next to the image
    """
    async with semaphore:
        print(f"→ Processing: {image_path}")
        caption = await generate_caption_for_image(client, image_path, caption_prompt)

        if not caption:
            print(f"⚠️  No caption generated for {image_path}")
            return

        output_path = os.path.splitext(image_path)[0] + ".txt"
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(caption)
            print(f"✅ Caption saved to: {output_path}")
        except Exception as e:
            print(f"Error writing caption for {image_path}: {e}")


async def process_directory(
    directory: str,
    max_concurrency: int = 5,
    model: str = "gpt-5.1",
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
            image_paths.append(full_path)

    if not image_paths:
        print(f"No images with extensions {sorted(IMAGE_EXTENSIONS)} found in {directory}")
        return

    print(f"Found {len(image_paths)} image(s) in {directory}")
    print(f"Using model: {model}")
    print(f"Max concurrency: {max_concurrency}")

    semaphore = asyncio.Semaphore(max_concurrency)

    tasks = [
        process_single_image(client, img_path, caption_prompt, semaphore)
        for img_path in image_paths
    ]

    await asyncio.gather(*tasks)


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python script.py <directory>")
        sys.exit(1)

    directory = sys.argv[1]

    if not os.path.isdir(directory):
        print(f"Error: {directory} is not a valid directory")
        sys.exit(1)

    asyncio.run(process_directory(directory))


if __name__ == "__main__":
    main()
