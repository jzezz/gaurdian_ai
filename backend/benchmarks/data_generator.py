"""Synthetic evaluation data generator for the Guardian AI benchmark suite.

Generates controllable benign images that a naive NSFW detector commonly
mis-classifies (medical diagrams, sculptures/art, traditional attire, and
skin-tone close-ups), plus a curated labeled text sample set.

Real-world datasets can be dropped into a folder and loaded via the
folder-based loader in ``dataset.py`` instead.
"""

import io
import random
from typing import Dict, List, Tuple

from PIL import Image, ImageDraw


def _gen_plain_landscape(seed: int) -> Image.Image:
    rng = random.Random(seed)
    img = Image.new("RGB", (224, 224))
    d = ImageDraw.Draw(img)
    sky = (rng.randint(80, 160), rng.randint(140, 200), rng.randint(200, 240))
    for y in range(112):
        d.line([(0, y), (224, y)], fill=tuple(c + int(y * 0.2) for c in sky))
    grass = (rng.randint(40, 90), rng.randint(120, 170), rng.randint(40, 90))
    for y in range(112, 224):
        d.line([(0, y), (224, y)], fill=grass)
    for _ in range(5):
        x, y = rng.randint(0, 150), rng.randint(20, 60)
        d.ellipse((x, y, x + rng.randint(25, 45), y + rng.randint(25, 45)),
                  fill=(rng.randint(200, 255), rng.randint(200, 255), rng.randint(200, 255)))
    return img


def _gen_medical_xray(seed: int) -> Image.Image:
    rng = random.Random(seed)
    img = Image.new("RGB", (224, 224), (15, 15, 25))
    d = ImageDraw.Draw(img)
    d.ellipse((62, 30, 162, 120), outline=(200, 200, 210), width=6)
    d.line((82, 120, 72, 205), fill=(200, 200, 210), width=8)
    d.line((142, 120, 152, 205), fill=(200, 200, 210), width=8)
    d.ellipse((70, 140, 100, 200), outline=(180, 180, 195), width=4)
    d.ellipse((124, 140, 154, 200), outline=(180, 180, 195), width=4)
    for _ in range(30):
        x, y = rng.randint(70, 160), rng.randint(40, 180)
        d.ellipse((x, y, x + rng.randint(1, 4), y + rng.randint(1, 4)),
                  outline=(140, 140, 160), width=1)
    return img


def _gen_sculpture(seed: int) -> Image.Image:
    rng = random.Random(seed)
    img = Image.new("RGB", (224, 224), (rng.randint(60, 90), rng.randint(70, 100), rng.randint(80, 110)))
    d = ImageDraw.Draw(img)
    base = (rng.randint(190, 230), rng.randint(185, 220), rng.randint(180, 215))
    d.ellipse((80, 40, 150, 105), fill=base)
    d.rectangle((100, 105, 130, 160), fill=base)
    d.rectangle((60, 160, 170, 170), fill=base)
    d.polygon([(90, 40), (110, 15), (130, 40)], fill=base)
    return img


def _gen_traditional_attire(seed: int) -> Image.Image:
    rng = random.Random(seed)
    img = Image.new("RGB", (224, 224), (rng.randint(200, 235), rng.randint(200, 235), rng.randint(200, 235)))
    d = ImageDraw.Draw(img)
    garment = (rng.randint(120, 190), rng.randint(30, 110), rng.randint(90, 160))
    d.polygon([(80, 70), (120, 60), (150, 70), (170, 220), (60, 220)], fill=garment)
    accent = (rng.randint(200, 255), rng.randint(150, 200), rng.randint(30, 90))
    d.ellipse((75, 75, 100, 105), fill=accent)
    d.ellipse((125, 75, 150, 105), fill=accent)
    for _ in range(20):
        x, y = rng.randint(70, 160), rng.randint(100, 210)
        d.rectangle((x, y, min(x + rng.randint(2, 8), 223), min(y + rng.randint(2, 8), 223)),
                    outline=accent, width=2)
    return img


def _gen_renaissance_painting(seed: int) -> Image.Image:
    rng = random.Random(seed)
    img = Image.new("RGB", (224, 224), (90, 70, 50))
    d = ImageDraw.Draw(img)
    for _ in range(800):
        x, y = rng.randint(0, 223), rng.randint(0, 223)
        r = rng.randint(1, 6)
        d.ellipse((x, y, x + r, y + r),
                  fill=(rng.randint(120, 220), rng.randint(90, 180), rng.randint(60, 140)))
    d.ellipse((84, 60, 140, 116), fill=(230, 200, 170))
    d.rectangle((90, 116, 134, 150), fill=(230, 200, 170))
    d.ellipse((70, 150, 154, 170), fill=(120, 90, 70))
    return img


def _gen_skin_tone_closeup(seed: int) -> Image.Image:
    """A skin-tone close-up (arm/hand) — classic naive-NSFW false positive."""
    rng = random.Random(seed)
    base = (rng.randint(200, 240), rng.randint(170, 210), rng.randint(140, 180))

    img = Image.new("RGB", (224, 224), base)
    # Add a subtle vertical gradient to simulate lighting
    for y in range(224):
        factor = 1.0 - (y / 224) * 0.25
        d = ImageDraw.Draw(img)
        d.line([(0, y), (224, y)], fill=(int(base[0] * factor), int(base[1] * factor), int(base[2] * factor)))

    d = ImageDraw.Draw(img)
    shade = tuple(max(0, c - 40) for c in base)
    highlight = tuple(min(255, c + 25) for c in base)
    # Arm shape
    d.polygon([(40, 224), (60, 40), (90, 30), (160, 40), (185, 224)], fill=base)
    # Hand
    d.ellipse((90, 15, 150, 75), fill=base)
    d.ellipse((70, 40, 100, 90), fill=base)
    d.ellipse((140, 40, 170, 90), fill=base)
    # Knuckle highlights
    for x, y in [(105, 35), (125, 32), (145, 35), (160, 50)]:
        d.ellipse((x, y, x + 12, y + 12), fill=highlight)
    # Wrist line
    d.line((75, 80, 165, 75), fill=shade, width=4)
    # Texture freckles
    for _ in range(150):
        x, y = rng.randint(50, 180), rng.randint(25, 200)
        d.rectangle((x, y, x + 2, y + 2), fill=(rng.randint(180, 230), rng.randint(150, 200), rng.randint(120, 170)))
    return img


def _gen_swimsuit_scene(seed: int) -> Image.Image:
    """Beach scene: person in swimwear near water — the PRD's core test case."""
    rng = random.Random(seed)
    img = Image.new("RGB", (224, 224))
    d = ImageDraw.Draw(img)
    # Sky gradient
    for y in range(110):
        d.line([(0, y), (224, y)], fill=(rng.randint(110, 160), rng.randint(175, 215), rng.randint(215, 245)))
    # Sea
    for y in range(110, 150):
        d.line([(0, y), (224, y)], fill=(rng.randint(30, 90), rng.randint(120, 180), rng.randint(180, 220)))
    # Sand
    for y in range(150, 224):
        d.line([(0, y), (224, y)], fill=(rng.randint(230, 245), rng.randint(215, 235), rng.randint(185, 210)))

    skin = (rng.randint(200, 235), rng.randint(175, 205), rng.randint(150, 180))
    shade = tuple(max(0, c - 35) for c in skin)
    # Head
    d.ellipse((96, 55, 128, 90), fill=skin)
    # Torso
    d.polygon([(94, 90), (130, 90), (138, 130), (86, 130)], fill=skin)
    # Arms raised
    d.polygon([(94, 92), (100, 96), (70, 130), (60, 122)], fill=skin)
    d.polygon([(130, 92), (124, 96), (154, 130), (164, 122)], fill=skin)
    # Legs
    d.polygon([(94, 130), (110, 130), (104, 205), (90, 205)], fill=skin)
    d.polygon([(114, 130), (130, 130), (134, 205), (120, 205)], fill=skin)
    # Swimsuit
    swimwear = (rng.randint(15, 80), rng.randint(50, 120), rng.randint(150, 220))
    d.rectangle((92, 118, 132, 148), fill=swimwear)
    d.line((112, 118, 112, 148), fill=shade, width=2)
    # Sun
    d.ellipse((30, 20, 60, 50), fill=(255, 240, 120))
    # Beach towel
    d.polygon([(150, 200), (215, 190), (220, 205), (155, 218)], fill=(rng.randint(200, 255), rng.randint(100, 200), rng.randint(100, 200)))
    return img


GENERATORS = {
    "plain_landscape": _gen_plain_landscape,
    "medical_xray": _gen_medical_xray,
    "sculpture": _gen_sculpture,
    "traditional_attire": _gen_traditional_attire,
    "renaissance_painting": _gen_renaissance_painting,
    "skin_tone_closeup": _gen_skin_tone_closeup,
    "swimsuit_scene": _gen_swimsuit_scene,
}

# Categories that are benign but are common false-positive triggers for
# naive NSFW detectors.
BENIGN_IMAGE_CATEGORIES = [
    "plain_landscape",
    "medical_xray",
    "sculpture",
    "traditional_attire",
    "renaissance_painting",
    "skin_tone_closeup",
    "swimsuit_scene",
]


def generate_benign_images(category: str, count: int, seed_offset: int = 0) -> List[Tuple[str, io.BytesIO]]:
    """Generate `count` synthetic images for a benign category.

    Returns a list of (label, BytesIO) tuples where label is 'benign'.
    """
    gen = GENERATORS[category]
    samples = []
    for i in range(count):
        buf = io.BytesIO()
        gen(seed_offset + i).save(buf, format="PNG")
        buf.seek(0)
        samples.append(("benign", buf))
    return samples


def generate_all_benign(count_per_category: int = 6) -> Dict[str, List[Tuple[str, io.BytesIO]]]:
    return {
        cat: generate_benign_images(cat, count_per_category, seed_offset=i * 100)
        for i, cat in enumerate(BENIGN_IMAGE_CATEGORIES)
    }


# --- Curated labeled text samples -----------------------------------------

TEXT_SAMPLES: List[Tuple[str, str]] = [
    # (text, label) where label is 'toxic' or 'benign'
    ("you are worthless and everyone hates you", "toxic"),
    ("i will find you and kill you", "toxic"),
    ("shut up you stupid idiot", "toxic"),
    ("go die in a fire", "toxic"),
    ("f*** off and never come back", "toxic"),
    ("kill yourself", "toxic"),
    ("you are a pathetic loser", "toxic"),
    ("I hope someone beats you senseless", "toxic"),
    ("The weather is pleasant today", "benign"),
    ("Thank you so much for your help", "benign"),
    ("Let's go for a walk in the park", "benign"),
    ("The report has been submitted on time", "benign"),
    ("I enjoy reading books on the weekend", "benign"),
    ("Congratulations on your new job", "benign"),
    ("The meeting is scheduled for 3pm", "benign"),
    ("This is a family vacation picture from Goa", "benign"),
    ("Subscribe for adult content, link in bio", "toxic"),
    ("Click here for x-rated videos and naked pics", "toxic"),
    ("breast cancer awareness month check yourself", "benign"),
    ("the statue of david is a famous renaissance sculpture", "benign"),
]
