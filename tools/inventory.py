#!/usr/bin/env python3
"""Technical inventory of all repository files (issue #2, stage 1)."""
import hashlib, json, os, sys
from pathlib import Path

from PIL import Image, ImageOps
import pillow_heif
pillow_heif.register_heif_opener()

REPO = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent.parent / "docs"
OUT.mkdir(parents=True, exist_ok=True)

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}

def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def dhash(img: Image.Image, size: int = 8) -> str:
    g = img.convert("L").resize((size + 1, size), Image.LANCZOS)
    px = list(g.getdata())
    bits = []
    for row in range(size):
        base = row * (size + 1)
        for col in range(size):
            bits.append("1" if px[base + col] > px[base + col + 1] else "0")
    return "".join(bits)

def hamming(a: str, b: str) -> int:
    return sum(x != y for x, y in zip(a, b))

records = []
for p in sorted(REPO.rglob("*")):
    if not p.is_file() or ".git" in p.parts:
        continue
    rel = p.relative_to(REPO).as_posix()
    rec = {
        "path": rel,
        "bytes": p.stat().st_size,
        "sha256": sha256(p),
        "ext": p.suffix.lower(),
    }
    if p.suffix.lower() in IMAGE_EXTS:
        try:
            with Image.open(p) as im:
                rec["format"] = im.format
                rec["width"], rec["height"] = im.size
                rec["mode"] = im.mode
                rec["orientation"] = ("landscape" if im.width > im.height
                                      else "portrait" if im.height > im.width else "square")
                rec["readable"] = True
                im.verify()
            with Image.open(p) as im:
                rec["dhash"] = dhash(im)
                ex = im.getexif()
                rec["exif_present"] = bool(ex)
                if ex:
                    rec["exif"] = {k: str(v)[:120] for k, v in ex.items()
                                   if k in (271, 272, 274, 306, 36867, 40962)}  # Make, Model, Orientation, DateTime, ...
        except Exception as e:
            rec["readable"] = False
            rec["error"] = f"{type(e).__name__}: {e}"
    elif p.suffix.lower() == ".pdf":
        try:
            from pypdf import PdfReader
            r = PdfReader(str(p))
            rec["format"] = "PDF"
            rec["pages"] = len(r.pages)
            meta = r.metadata or {}
            rec["pdf_meta"] = {str(k): str(v)[:160] for k, v in meta.items()}
            texts = []
            for i, page in enumerate(r.pages):
                try:
                    t = (page.extract_text() or "").strip()
                except Exception:
                    t = ""
                texts.append({"page": i + 1, "chars": len(t), "sample": t[:400]})
                rec.setdefault("images_on_page", []).append(len(list(page.images)))
            rec["pdf_text"] = texts
        except Exception as e:
            rec["error"] = f"{type(e).__name__}: {e}"
    elif p.suffix.lower() == ".txt":
        rec["format"] = "text"
        try:
            t = p.read_text(encoding="utf-8", errors="replace")
            rec["chars"] = len(t)
            rec["lines"] = t.count("\n") + 1
        except Exception as e:
            rec["error"] = str(e)
    records.append(rec)

# exact duplicates by sha256
by_hash = {}
for r in records:
    by_hash.setdefault(r["sha256"], []).append(r["path"])
exact = {h: ps for h, ps in by_hash.items() if len(ps) > 1}

# near-duplicates by dhash among images
imgs = [r for r in records if "dhash" in r]
near = []
for i in range(len(imgs)):
    for j in range(i + 1, len(imgs)):
        d = hamming(imgs[i]["dhash"], imgs[j]["dhash"])
        if d <= 10:
            near.append({"a": imgs[i]["path"], "b": imgs[j]["path"], "dhash_distance": d,
                         "same_bytes": imgs[i]["sha256"] == imgs[j]["sha256"],
                         "dims_a": [imgs[i]["width"], imgs[i]["height"]],
                         "dims_b": [imgs[j]["width"], imgs[j]["height"]]})
near.sort(key=lambda x: x["dhash_distance"])

summary = {
    "total_files": len(records),
    "images": sum(1 for r in records if "dhash" in r),
    "unreadable": [r["path"] for r in records if r.get("readable") is False],
    "exact_duplicate_groups": list(exact.values()),
    "near_duplicate_pairs": near,
}
(OUT / "inventory.json").write_text(json.dumps({"summary": summary, "records": records},
                                               ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False, indent=2))
print("\n--- per-file ---")
for r in records:
    if "dhash" in r:
        print(f'{r["path"][:75]:<75} {r["format"]:<5} {r["width"]}x{r["height"]} {r["bytes"]:>8} {r.get("exif_present", False)}')
    else:
        print(f'{r["path"][:75]:<75} {r.get("format", r["ext"]):<5} {"-":>9} {r["bytes"]:>8}')
