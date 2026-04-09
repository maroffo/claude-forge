# ABOUTME: Shared Gemini image generation script for cover-image and table-image skills
# ABOUTME: Invoked via uv run --with google-genai,Pillow; supports prompt, --ar, --size, -o args
#
# /// script
# requires-python = ">=3.11"
# dependencies = ["google-genai", "Pillow"]
# ///

"""Generate an image using Gemini's image generation model.

Usage:
    uv run ~/.claude/skills/_generate_image.py "your prompt" -o output.png
    echo "your prompt" | uv run ~/.claude/skills/_generate_image.py -o output.png
"""

import argparse
import io
import os
import re
import sys
from datetime import datetime
from pathlib import Path

from PIL import Image as PILImage

from google import genai
from google.genai import types


def _load_dotenv_fallback() -> None:
    """Load ~/.env if GEMINI_API_KEY / GOOGLE_API_KEY not already in env."""
    if os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
        return
    env_file = Path.home() / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip("'\"")
        if key in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
            os.environ[key] = value


_load_dotenv_fallback()


ASPECT_RATIO_SIZES = {
    "1:1":   {"1K": (1024, 1024), "2K": (2048, 2048), "4K": (4096, 4096)},
    "16:9":  {"1K": (1024, 576),  "2K": (2048, 1152), "4K": (4096, 2304)},
    "9:16":  {"1K": (576, 1024),  "2K": (1152, 2048), "4K": (2304, 4096)},
    "4:3":   {"1K": (1024, 768),  "2K": (2048, 1536), "4K": (4096, 3072)},
    "3:4":   {"1K": (768, 1024),  "2K": (1536, 2048), "4K": (3072, 4096)},
    "3:2":   {"1K": (1024, 683),  "2K": (2048, 1365), "4K": (4096, 2731)},
    "2:3":   {"1K": (683, 1024),  "2K": (1365, 2048), "4K": (2731, 4096)},
    "24:9":  {"1K": (1024, 384),  "2K": (2048, 768),  "4K": (4096, 1536)},
}

MODEL = "gemini-3-pro-image-preview"


def extract_ar_from_prompt(prompt: str) -> tuple[str, str | None]:
    """Extract --ar from prompt text (Midjourney-style)."""
    match = re.search(r"--ar\s+(\d+:\d+)", prompt)
    if match:
        ar = match.group(1)
        cleaned = prompt[: match.start()] + prompt[match.end() :]
        return cleaned.strip(), ar
    return prompt, None


def get_api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        print("Error: GEMINI_API_KEY or GOOGLE_API_KEY must be set", file=sys.stderr)
        sys.exit(1)
    return key


def generate_output_name(ar: str | None) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = f"_{ar.replace(':', 'x')}" if ar else ""
    return f"generated{suffix}_{ts}.png"


def main():
    parser = argparse.ArgumentParser(description="Generate an image via Gemini API")
    parser.add_argument("prompt", nargs="?", help="Image prompt (or pipe via stdin)")
    parser.add_argument("-o", "--output", help="Output filename (default: auto-named)")
    parser.add_argument("--ar", help="Aspect ratio (e.g. 16:9, 24:9)")
    parser.add_argument(
        "--size",
        choices=["1K", "2K", "4K"],
        default="1K",
        help="Output size tier (default: 1K)",
    )
    args = parser.parse_args()

    # Get prompt from arg or stdin
    prompt = args.prompt
    if not prompt:
        if sys.stdin.isatty():
            print("Error: provide prompt as argument or via stdin", file=sys.stderr)
            sys.exit(1)
        prompt = sys.stdin.read().strip()

    if not prompt:
        print("Error: empty prompt", file=sys.stderr)
        sys.exit(1)

    # Extract --ar from prompt if present
    prompt, prompt_ar = extract_ar_from_prompt(prompt)
    ar = args.ar or prompt_ar

    # Determine output path
    output = args.output or generate_output_name(ar)

    # Initialize client
    client = genai.Client(api_key=get_api_key())

    # Generate image
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
        ),
    )

    # Find and save image
    if not response.candidates or not response.candidates[0].content.parts:
        print("Error: no response from model", file=sys.stderr)
        sys.exit(1)

    image_saved = False
    for part in response.candidates[0].content.parts:
        if part.inline_data and part.inline_data.mime_type.startswith("image/"):
            image_data = part.inline_data.data
            pil_image = PILImage.open(io.BytesIO(image_data))

            # Resize if aspect ratio specified
            if ar and ar in ASPECT_RATIO_SIZES:
                size = ASPECT_RATIO_SIZES[ar].get(args.size, ASPECT_RATIO_SIZES[ar]["1K"])
                pil_image = pil_image.resize(size, PILImage.LANCZOS)

            pil_image.save(output)
            image_saved = True
            print(output)
            break

    if not image_saved:
        # Print any text response for debugging
        for part in response.candidates[0].content.parts:
            if part.text:
                print(f"Model response (no image): {part.text}", file=sys.stderr)
        print("Error: no image in response", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
