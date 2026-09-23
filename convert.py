from pathlib import Path
import shutil

from PIL import Image, ImageOps

# ---------------------------------------------------------------------------
# SETTINGS — change these values as needed
# ---------------------------------------------------------------------------

INPUT_FOLDER = Path("./original_images")
OUTPUT_FOLDER = Path("./images")

# Higher = better quality and larger files.
#   75–82 = high quality
#   65–74 = good web quality
#   55–64 = smaller files
WEBP_QUALITY = 82

# Images larger than this are proportionally resized.
# Lower values save significant space.
# Suggested values: 1800, 1600, 1400, 1200, or 1000.
MAX_LONG_EDGE = 1600

# True preserves transparent areas.
# False replaces transparency with BACKGROUND_COLOR and usually saves space.
PRESERVE_TRANSPARENCY = True
BACKGROUND_COLOR = (255, 255, 255)

# Skip an image when its exact corresponding output path already exists.
#
# Example:
#   images/gallery/events/photo.jpg
# maps to:
#   converted_webp/gallery/events/photo.webp
#
# It will only be skipped if that exact output path exists.
SKIP_EXISTING = True

# Keep this False when using SKIP_EXISTING. Setting it to True deletes all
# existing output files before conversion, so there would be nothing to skip.
CLEAR_OUTPUT_FOLDER = False

# Compression effort from 0 to 6.
# Higher is slower but may produce smaller files at the same quality.
WEBP_METHOD = 6

SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".gif",
    ".tif",
    ".tiff",
}


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

if not INPUT_FOLDER.exists():
    raise FileNotFoundError(
        f"Input folder does not exist: {INPUT_FOLDER.resolve()}"
    )

if CLEAR_OUTPUT_FOLDER and OUTPUT_FOLDER.exists():
    shutil.rmtree(OUTPUT_FOLDER)

OUTPUT_FOLDER.mkdir(exist_ok=True, parents=True)


# ---------------------------------------------------------------------------
# Conversion
# ---------------------------------------------------------------------------

converted_count = 0
skipped_count = 0
failed_count = 0
new_output_bytes = 0

for path in sorted(INPUT_FOLDER.rglob("*")):
    if not path.is_file() or path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        continue

    # Preserve the complete relative directory structure.
    relative_path = path.relative_to(INPUT_FOLDER)
    output_path = OUTPUT_FOLDER / relative_path.with_suffix(".webp")

    # This checks the exact output path, including all parent directories.
    # An image with the same filename elsewhere will not cause this one to
    # be skipped.
    if SKIP_EXISTING and output_path.is_file():
        skipped_count += 1
        print(f"Skipped existing: {path} -> {output_path}")
        continue

    try:
        output_path.parent.mkdir(exist_ok=True, parents=True)

        with Image.open(path) as source:
            # For animated images, use the first frame.
            try:
                source.seek(0)
            except EOFError:
                pass

            # Apply EXIF orientation before deleting the metadata.
            source = ImageOps.exif_transpose(source)
            source.load()

            has_transparency = (
                source.mode in {"RGBA", "LA"}
                or (
                    source.mode == "P"
                    and "transparency" in source.info
                )
                or "A" in source.getbands()
            )

            if has_transparency and PRESERVE_TRANSPARENCY:
                output_image = source.convert("RGBA")

            elif has_transparency:
                rgba_image = source.convert("RGBA")

                background = Image.new(
                    "RGBA",
                    rgba_image.size,
                    (*BACKGROUND_COLOR, 255),
                )

                output_image = Image.alpha_composite(
                    background,
                    rgba_image,
                ).convert("RGB")

                rgba_image.close()
                background.close()

            else:
                output_image = source.convert("RGB")

        try:
            # Resize proportionally only when the image exceeds the limit.
            width, height = output_image.size
            longest_edge = max(width, height)

            if longest_edge > MAX_LONG_EDGE:
                scale = MAX_LONG_EDGE / longest_edge

                new_size = (
                    max(1, round(width * scale)),
                    max(1, round(height * scale)),
                )

                resized_image = output_image.resize(
                    new_size,
                    Image.Resampling.LANCZOS,
                    reducing_gap=3.0,
                )

                output_image.close()
                output_image = resized_image

            # Remove inherited metadata such as EXIF, ICC profiles, XMP,
            # comments, DPI information, and source-format information.
            output_image.info.clear()

            output_image.save(
                output_path,
                format="WEBP",
                quality=WEBP_QUALITY,
                alpha_quality=WEBP_QUALITY,
                method=WEBP_METHOD,
                lossless=False,

                # Explicitly prevent metadata from being written.
                exif=b"",
                icc_profile=b"",
                xmp=b"",
            )

        finally:
            output_image.close()

        output_size = output_path.stat().st_size
        new_output_bytes += output_size
        converted_count += 1

        print(
            f"Converted: {path} -> {output_path} "
            f"({output_size / 1024:.1f} KB)"
        )

    except Exception as error:
        failed_count += 1
        print(f"Failed: {path} ({error})")


# ---------------------------------------------------------------------------
# Calculate complete output-folder size
# ---------------------------------------------------------------------------

total_output_bytes = sum(
    file.stat().st_size
    for file in OUTPUT_FOLDER.rglob("*")
    if file.is_file()
)


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

print()
print(f"Converted files:       {converted_count}")
print(f"Skipped existing:      {skipped_count}")
print(f"Failed files:          {failed_count}")
print(f"New files size:        {new_output_bytes / 1_000_000:.2f} MB")
print(f"Complete folder size:  {total_output_bytes / 1_000_000:.2f} MB")
print(f"Output folder:         {OUTPUT_FOLDER.resolve()}")

if total_output_bytes >= 25_000_000:
    print()
    print("The complete output folder is above 25 MB.")
    print("Lower WEBP_QUALITY and/or MAX_LONG_EDGE, then run it again.")
    print(
        "To regenerate existing images with the new settings, set "
        "SKIP_EXISTING = False."
    )
else:
    print()
    print("The complete output folder is below 25 MB.")