"""Folder-based real-image dataset loader.

Expected layout::

    dataset/
        benign/
            *.jpg|*.png|*.jpeg|*.webp
        toxic/            (optional — images that should be flagged)
            *.jpg|*.png|*.jpeg|*.webp

Each folder determines the ground-truth label. Use this to validate the
synthetic benchmark with real-world images later.
"""

import io
import os
from typing import Dict, List, Tuple

from PIL import Image

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def load_folder_dataset(root: str) -> Dict[str, List[Tuple[str, io.BytesIO]]]:
    """Load a folder dataset. Returns {label: [(label, BytesIO), ...]}."""
    dataset: Dict[str, List[Tuple[str, io.BytesIO]]] = {}
    if not os.path.isdir(root):
        return dataset

    for label in os.listdir(root):
        label_dir = os.path.join(root, label)
        if not os.path.isdir(label_dir):
            continue
        samples = []
        for fname in sorted(os.listdir(label_dir)):
            ext = os.path.splitext(fname)[1].lower()
            if ext not in IMAGE_EXTS:
                continue
            path = os.path.join(label_dir, fname)
            try:
                with Image.open(path) as img:
                    img = img.convert("RGB")
                    buf = io.BytesIO()
                    img.save(buf, format="JPEG")
                    buf.seek(0)
                samples.append((label, buf))
            except Exception as e:
                print(f"Skipping {path}: {e}")
        if samples:
            dataset[label] = samples
    return dataset
