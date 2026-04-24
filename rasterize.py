#!/usr/bin/env python3
"""
Create a raster image from all images in a directory.

Usage:
    python rasterize.py <columns> <rows> <width> <height> <directory>

Arguments:
    columns     Number of columns in the raster (int)
    rows        Number of rows in the raster (int)
    width       Width of the final image in pixels (int)
    height      Height of the final image in pixels (int)
    directory   Path to the folder containing images

Options:
    --output    Output file path (default: <directory_name>.jpg in current directory)
"""

import argparse
from pathlib import Path
from PIL import Image

from image_paths import resolve_image_path

# Try enabling AVIF support
try:
    import pillow_avif  # noqa: F401
except ImportError:
    pass

# Supported file extensions
IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".avif"
}


def find_images(directory: Path):
    """Return a sorted list of image paths in the directory."""
    images = [
        p for p in directory.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    ]
    images.sort()
    return images


def create_raster(
    image_paths,
    columns: int,
    rows: int,
    total_width: int,
    total_height: int,
    output_path: Path,
):
    """Create the raster image and save it to output_path."""
    num_cells = columns * rows
    image_paths = image_paths[:num_cells]

    cell_width = total_width // columns
    cell_height = total_height // rows

    canvas = Image.new("RGB", (total_width, total_height), (0, 0, 0))

    for idx, img_path in enumerate(image_paths):
        try:
            with Image.open(img_path) as img:
                img = img.convert("RGB")
                w, h = img.size

                scale = min(cell_width / w, cell_height / h)
                new_w = int(w * scale)
                new_h = int(h * scale)

                resized = img.resize((new_w, new_h), Image.LANCZOS)

                row = idx // columns
                col = idx % columns

                cell_x = col * cell_width
                cell_y = row * cell_height

                offset_x = cell_x + (cell_width - new_w) // 2
                offset_y = cell_y + (cell_height - new_h) // 2

                canvas.paste(resized, (offset_x, offset_y))

        except Exception as e:
            print(f"Warning: Could not process {img_path}: {e}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path)
    print(f"Saved raster image to: {output_path}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Create a raster image from all images in a directory."
    )

    parser.add_argument("columns", type=int, help="Number of columns")
    parser.add_argument("rows", type=int, help="Number of rows")
    parser.add_argument("width", type=int, help="Output image width")
    parser.add_argument("height", type=int, help="Output image height")

    # DIRECTORY IS NOW THE LAST PARAMETER
    parser.add_argument("directory", type=str, help="Directory with images")

    parser.add_argument(
        "--output",
        type=str,
        help="Output file path (default: <directory_name>.jpg in current directory)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    directory = resolve_image_path(args.directory)
    if not directory.is_dir():
        raise SystemExit(f"Error: {directory} is not a valid directory.")

    image_paths = find_images(directory)
    if not image_paths:
        raise SystemExit("Error: No supported images found in the directory.")

    if args.output:
        output_path = Path(args.output)
    else:
        output_name = f"{directory.name}.jpg"
        output_path = Path.cwd() / output_name

    create_raster(
        image_paths=image_paths,
        columns=args.columns,
        rows=args.rows,
        total_width=args.width,
        total_height=args.height,
        output_path=output_path,
    )


if __name__ == "__main__":
    main()
