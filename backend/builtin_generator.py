import colorsys
import math
import random
import textwrap

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps

MODEL = "builtin/text-on-shapes"
SIZE = (1024, 1024)
MARGIN = 64
TEXT_LIGHTNESS = 0.86
TEXT_SATURATION = 1.0
TEXT_STROKE_COLOR = (0, 0, 0)
BLUR_RADIUS = 4
GRAIN_STRENGTH = 0.26
FONT_PATHS = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/System/Library/Fonts/Menlo.ttc",
    "C:/Windows/Fonts/consola.ttf",
)


def _font(size: int):
    for path in FONT_PATHS:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


def _muted_color(rng: random.Random, lightness: float):
    red, green, blue = colorsys.hls_to_rgb(rng.random(), lightness, rng.uniform(0.10, 0.30))
    return round(red * 255), round(green * 255), round(blue * 255)


def _text_color(rng: random.Random):
    red, green, blue = colorsys.hls_to_rgb(rng.random(), TEXT_LIGHTNESS, TEXT_SATURATION)
    return round(red * 255), round(green * 255), round(blue * 255)


def _gradient(size: tuple[int, int], rng: random.Random):
    start = _muted_color(rng, rng.uniform(0.02, 0.16))
    end = _muted_color(rng, rng.uniform(0.84, 0.98))
    if rng.random() < 0.5:
        start, end = end, start
    # Rotate a larger gradient and crop its center so the rotation leaves no empty corners.
    gradient = Image.linear_gradient("L").resize((512, 512))
    gradient = gradient.rotate(rng.uniform(0, 360), resample=Image.Resampling.BICUBIC).crop((128, 128, 384, 384))
    # The center crop only covers part of the original range, so stretch it back to 0-255.
    gradient = ImageOps.autocontrast(gradient).resize(size)
    return Image.composite(Image.new("RGB", size, end), Image.new("RGB", size, start), gradient)


def _add_grain(image: Image.Image, rng: random.Random):
    # Seeded noise instead of Image.effect_noise so the same seed renders the same image.
    noise = Image.frombytes("L", image.size, rng.randbytes(image.size[0] * image.size[1]))
    noise = noise.point(lambda value: round(128 + (value - 128) * GRAIN_STRENGTH))
    return ImageChops.add(image, noise.convert("RGB"), offset=-128)


def _shape_mask(size: tuple[int, int], rng: random.Random):
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    width, height = size
    if rng.random() < 0.5:
        draw.ellipse((0, 0, width - 1, height - 1), fill=255)
    else:
        angle = rng.uniform(0, math.pi)
        cos_angle, sin_angle = math.cos(angle), math.sin(angle)
        aspect = rng.uniform(0.25, 1)
        # Scale the rotated rectangle to fit inside the mask so its corners are not clipped.
        half_width = min(
            width / 2 / (abs(cos_angle) + aspect * abs(sin_angle)),
            height / 2 / (abs(sin_angle) + aspect * abs(cos_angle)),
        )
        half_height = half_width * aspect
        corners = [(-half_width, -half_height), (half_width, -half_height), (half_width, half_height), (-half_width, half_height)]
        draw.polygon(
            [(width / 2 + x * cos_angle - y * sin_angle, height / 2 + x * sin_angle + y * cos_angle) for x, y in corners],
            fill=255,
        )
    return mask


def _draw_text(image: Image.Image, text: str, color: tuple[int, int, int]):
    max_width = SIZE[0] - 2 * MARGIN
    max_height = SIZE[1] - 2 * MARGIN
    for font_size in range(72, 11, -4):
        font = _font(font_size)
        line_height = font_size * 1.25
        lines = textwrap.wrap(text, max(1, int(max_width // font.getlength("M")))) or [""]
        if len(lines) * line_height <= max_height:
            break
    lines = lines[: max(1, int(max_height // line_height))]

    ImageDraw.Draw(image).multiline_text(
        (SIZE[0] / 2, SIZE[1] / 2),
        "\n".join(lines),
        font=font,
        fill=color,
        anchor="mm",
        align="center",
        spacing=font_size * 0.25,
        stroke_width=max(2, font_size // 16),
        stroke_fill=TEXT_STROKE_COLOR,
    )


def generate(description: str, seed=None) -> Image.Image:
    rng = random.Random(seed)
    image = _gradient(SIZE, rng)
    for _ in range(rng.randint(5, 15)):
        width, height = rng.randint(384, 1024), rng.randint(384, 1024)
        position = (rng.randint(-width // 2, SIZE[0] - width // 2), rng.randint(-height // 2, SIZE[1] - height // 2))
        image.paste(_gradient((width, height), rng), position, _shape_mask((width, height), rng))
    image = _add_grain(image.filter(ImageFilter.GaussianBlur(BLUR_RADIUS)), rng)
    _draw_text(image, description, _text_color(rng))
    return image
