#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regenerate derived assets for the BORIS media library (issue #2).

Reads docs/assets-manifest.json and rebuilds, without touching any original:
  assets/processed/web/            — web JPEG copies (long edge <= 1600, q80)
  assets/processed/thumbs/         — thumbnails (long edge <= 480, q78)
  assets/processed/contact-sheets/ — contact sheets with readable IDs + filenames
Optional: --heic-working writes full-res review JPEGs of the HEIC sources
          into assets/processed/heic-working/ (not committed; originals kept).

Requires: Pillow, pillow-heif (для открытия HEIC-исходников).
Usage:    python3 tools/generate_derived.py [--heic-working]
"""
import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

try:
    import pillow_heif  # noqa: F401 — needed to open HEIC originals
    pillow_heif.register_heif_opener()
except ImportError:
    print("ПРЕДУПРЕЖДЕНИЕ: pillow-heif не установлен — HEIC-файлы не будут обработаны "
          "(pip install pillow-heif)", file=sys.stderr)

REPO = Path(__file__).resolve().parent.parent
MANIFEST = REPO / "docs" / "assets-manifest.json"
WEB_DIR = REPO / "assets" / "processed" / "web"
THUMB_DIR = REPO / "assets" / "processed" / "thumbs"
SHEET_DIR = REPO / "assets" / "processed" / "contact-sheets"
HEIC_DIR = REPO / "assets" / "processed" / "heic-working"

WEB_MAX = 1600
WEB_Q = 80
THUMB_MAX = 480
THUMB_Q = 78

SHEETS = [
    ("sheet-01-heic-source.jpg", "HEIC-исходники (IMG_1527…IMG_1539) — рабочие кадры серии барной стойки и скальной стены", [f"P{i:02d}" for i in range(1, 11)]),
    ("sheet-02-rock-surfaces.jpg", "Скальные поверхности и фактуры", [f"P{i:02d}" for i in range(11, 18)]),
    ("sheet-03-rock-relief-gold.jpg", "Рельефная панель с золотыми прожилками (серия photo_5–photo_10)", [f"P{i:02d}" for i in range(18, 24)]),
    ("sheet-04-objects-planters-panels.jpg", "Объекты, кашпо и декоративные панели", [f"P{i:02d}" for i in range(24, 30)]),
    ("sheet-05-themed-sculptures-1.jpg", "Тематические скульптуры, часть 1 (этапы производства)", [f"P{i:02d}" for i in range(30, 37)]),
    ("sheet-06-themed-sculptures-2.jpg", "Тематические скульптуры, часть 2", [f"P{i:02d}" for i in range(37, 43)]),
    ("sheet-07-props-and-references.jpg", "Реквизит и материалы с внешними водяными знаками (проверить происхождение)", [f"P{i:02d}" for i in range(43, 47)]),
]

FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def font(size: int, bold: bool = False):
    idx = 1 if bold else 0
    try:
        return ImageFont.truetype(FONT_PATHS[idx], size)
    except OSError:
        return ImageFont.load_default()


def save_web(im: Image.Image, dest: Path, max_edge: int, quality: int):
    im = im.convert("RGB")
    im.thumbnail((max_edge, max_edge), Image.LANCZOS)
    dest.parent.mkdir(parents=True, exist_ok=True)
    im.save(dest, "JPEG", quality=quality, optimize=True, progressive=True)
    return dest.stat().st_size


def fit_text(draw, text, fnt, width):
    if draw.textlength(text, font=fnt) <= width:
        return text
    while text and draw.textlength(text + "…", font=fnt) > width:
        text = text[:-1]
    return text + "…"


def wrap(draw, text, fnt, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=fnt) <= width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = fit_text(draw, w, fnt, width)
    if cur:
        lines.append(cur)
    return lines


def build_sheet(records_by_id, dest: Path, title: str, ids, sheet_no: str):
    cols = 4
    cell_w, thumb_h, cap_h = 800, 580, 132
    cell_h = thumb_h + cap_h
    rows = (len(ids) + cols - 1) // cols
    header_h, footer_h = 130, 60
    W = cols * cell_w
    H = header_h + rows * cell_h + footer_h
    sheet = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(sheet)

    d.rectangle([0, 0, W, header_h], fill=(24, 24, 28))
    d.text((40, 30), title, font=font(46, True), fill="white")
    d.text((40, 84), f"BORIS · визуальный аудит 2026-11-09 · {sheet_no} · все исходники сохранены без изменений",
           font=font(28), fill=(190, 190, 195))

    for i, pid in enumerate(ids):
        rec = records_by_id[pid]
        cx, cy = (i % cols) * cell_w, header_h + (i // cols) * cell_h
        # thumb
        cell = Image.new("RGB", (cell_w, thumb_h), (250, 250, 250))
        src = REPO / rec["original_path"]
        with Image.open(src) as im:
            im = im.convert("RGB")
            im.thumbnail((cell_w - 24, thumb_h - 24), Image.LANCZOS)
            cell.paste(im, ((cell_w - im.width) // 2, (thumb_h - im.height) // 2))
        sheet.paste(cell, (cx, cy))
        d.rectangle([cx, cy, cx + cell_w - 1, cy + cell_h - 1], outline=(210, 210, 215))
        # caption
        y = cy + thumb_h + 6
        slug = rec["derived"]["web"].rsplit("/", 1)[-1].split(".", 1)[0].split("-", 1)[1]
        d.text((cx + 14, y), f'{pid} · {slug}',
               font=font(32, True), fill=(20, 20, 20))
        name = fit_text(d, rec["filename"], font(26), cell_w - 28)
        d.text((cx + 14, y + 40), name, font=font(26), fill=(60, 60, 65))
        status = rec["status"]
        extra = f'{rec["width"]}×{rec["height"]} · {rec["bytes"] // 1024} КБ · {rec["format"]} · {status}'
        if rec.get("contains_people"):
            extra += " · есть люди"
        if rec.get("watermark"):
            extra += f' · знак: {rec["watermark"]}'
        d.text((cx + 14, y + 76), extra, font=font(25), fill=(120, 120, 128))

    d.text((40, H - 48), "ID соответствует docs/assets-manifest.json · описание каждого кадра — там же",
           font=font(26), fill=(120, 120, 128))
    dest.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(dest, "JPEG", quality=86, optimize=True, progressive=True)
    return dest.stat().st_size


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--heic-working", action="store_true",
                    help="also write full-res review JPEGs of HEIC originals (not committed)")
    args = ap.parse_args()

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    images = [r for r in manifest["files"] if r.get("derived")]
    by_id = {r["id"]: r for r in manifest["files"]}

    total = {"web": 0, "thumb": 0, "sheets": 0}
    for rec in images:
        src = REPO / rec["original_path"]
        with Image.open(src) as im:
            total["web"] += save_web(im, REPO / rec["derived"]["web"], WEB_MAX, WEB_Q)
        with Image.open(src) as im:
            total["thumb"] += save_web(im, REPO / rec["derived"]["thumb"], THUMB_MAX, THUMB_Q)
        print(f'{rec["id"]} -> web+thumb: {rec["filename"]}')

    for i, (fname, title, ids) in enumerate(SHEETS, 1):
        size = build_sheet(by_id, SHEET_DIR / fname, title, ids, f"лист {i}/{len(SHEETS)}")
        total["sheets"] += size
        print(f"sheet {fname}: {size // 1024} КБ")

    if args.heic_working:
        for rec in images:
            if rec["original_path"].lower().endswith(".heic"):
                with Image.open(REPO / rec["original_path"]) as im:
                    out = HEIC_DIR / (Path(rec["original_path"]).stem + ".jpg")
                    im.convert("RGB").save(out, "JPEG", quality=90)
                print("heic-working:", out.name)

    print(f"\nИтого: web={total['web'] // 1024} КБ, thumbs={total['thumb'] // 1024} КБ, "
          f"contact-sheets={total['sheets'] // 1024} КБ")
    return 0


if __name__ == "__main__":
    sys.exit(main())
