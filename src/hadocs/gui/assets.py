from pathlib import Path
import sys
import tkinter as tk

LOGO_DEBUG = []


def _project_roots():
    roots = [Path(getattr(sys, "_MEIPASS", Path.cwd())), Path.cwd()]
    try:
        roots.extend(Path(__file__).resolve().parents)
    except Exception:
        pass

    unique = []
    seen = set()
    for root in roots:
        try:
            resolved = root.resolve()
        except Exception:
            resolved = root
        if resolved not in seen:
            unique.append(root)
            seen.add(resolved)
    return unique


def app_path(*parts):
    for root in _project_roots():
        candidate = root.joinpath(*parts)
        if candidate.exists():
            return candidate
    return Path.cwd().joinpath(*parts)


def find_logo_file():
    names = ("logo.png", "Logo.png", "HADocs.png", "hadocs.png", "logo.svg", "icon.png", "Icon.png")
    for root in _project_roots():
        for name in names:
            candidate = root / "docs" / "images" / name
            if candidate.exists():
                return candidate

    for root in _project_roots():
        images = root / "docs" / "images"
        if not images.exists():
            continue
        try:
            matches = sorted(
                p for p in images.iterdir()
                if p.is_file() and "logo" in p.name.lower() and p.suffix.lower() in {".png", ".svg", ".gif"}
            )
            if matches:
                return matches[0]
        except Exception:
            continue
    return None


def load_logo_image(max_size=170):
    path = find_logo_file()
    if path is None:
        return None

    try:
        from PIL import Image, ImageTk
        if path.suffix.lower() == ".svg":
            try:
                import io
                import cairosvg
                png_bytes = cairosvg.svg2png(url=str(path))
                img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
            except Exception:
                return None
        else:
            img = Image.open(path).convert("RGBA")

        img.thumbnail((max_size, max_size))
        canvas = Image.new("RGBA", (max_size, max_size), (0, 0, 0, 0))
        canvas.alpha_composite(img, ((max_size - img.width) // 2, (max_size - img.height) // 2))
        return ImageTk.PhotoImage(canvas)
    except Exception:
        pass

    if path.suffix.lower() == ".png":
        try:
            image = tk.PhotoImage(file=str(path))
            factor = max(1, int(max(image.width(), image.height()) / max_size))
            return image.subsample(factor, factor) if factor > 1 else image
        except Exception:
            return None
    return None
