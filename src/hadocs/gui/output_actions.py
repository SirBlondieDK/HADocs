from pathlib import Path
import os
import subprocess
import sys
import webbrowser


def output_paths(output_dir: str | Path = "output") -> dict[str, Path]:
    output = Path(output_dir)
    return {
        "output_dir": output,
        "dashboard": output / "index.html",
        "explorer": output / "explorer" / "index.html",
        "markdown": output / "index.md",
        "knowledge": output / "knowledge",
    }


def output_status(output_dir: str | Path = "output") -> dict[str, bool]:
    paths = output_paths(output_dir)
    return {name: path.exists() for name, path in paths.items()}


def completion_message(output_dir: str | Path = "output") -> str:
    paths = output_paths(output_dir)
    status = output_status(output_dir)

    lines = [
        "Documentation successfully generated.",
        "",
        f"Dashboard: {paths['dashboard']}" if status["dashboard"] else "Dashboard: not found",
        f"Explorer: {paths['explorer']}" if status["explorer"] else "Explorer: not found",
        f"Knowledge Pack: {paths['knowledge']}" if status["knowledge"] else "Knowledge Pack: not found",
        f"Markdown: {paths['markdown']}" if status["markdown"] else "Markdown: not found",
    ]

    return "\n".join(lines)


def open_path(path: str | Path) -> bool:
    path = Path(path)

    if not path.exists():
        return False

    if path.is_file() and path.suffix.lower() in {".html", ".htm"}:
        webbrowser.open(path.resolve().as_uri())
        return True

    if sys.platform.startswith("win"):
        os.startfile(path)  # type: ignore[attr-defined]
        return True

    if sys.platform == "darwin":
        subprocess.Popen(["open", str(path)])
        return True

    subprocess.Popen(["xdg-open", str(path)])
    return True


def open_dashboard(output_dir: str | Path = "output") -> bool:
    return open_path(output_paths(output_dir)["dashboard"])


def open_explorer(output_dir: str | Path = "output") -> bool:
    return open_path(output_paths(output_dir)["explorer"])


def open_markdown(output_dir: str | Path = "output") -> bool:
    return open_path(output_paths(output_dir)["markdown"])


def open_output_folder(output_dir: str | Path = "output") -> bool:
    return open_path(output_paths(output_dir)["output_dir"])
