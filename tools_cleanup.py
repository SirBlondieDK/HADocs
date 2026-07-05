from pathlib import Path
import shutil


GENERATED_DIRS = [
    ".pytest_tmp",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
]

GENERATED_FILE_PATTERNS = [
    "*.pyc",
]


def remove_dir(path: Path) -> bool:
    if path.exists() and path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
        return True
    return False


def remove_pycache(root: Path) -> int:
    count = 0
    for folder in root.rglob("__pycache__"):
        if folder.is_dir():
            shutil.rmtree(folder, ignore_errors=True)
            count += 1
    return count


def remove_generated_files(root: Path) -> int:
    count = 0
    for pattern in GENERATED_FILE_PATTERNS:
        for file in root.rglob(pattern):
            if file.is_file():
                try:
                    file.unlink()
                    count += 1
                except OSError:
                    pass
    return count


def main() -> None:
    root = Path.cwd()
    removed = []

    for name in GENERATED_DIRS:
        if remove_dir(root / name):
            removed.append(name)

    pycache_count = remove_pycache(root)
    pyc_count = remove_generated_files(root)

    print("HADocs cleanup complete.")
    if removed:
        print("Removed folders:")
        for item in removed:
            print(f"- {item}")

    print(f"Removed __pycache__ folders: {pycache_count}")
    print(f"Removed .pyc files: {pyc_count}")
    print("")
    print("Note: output/, cache/ and config.json are intentionally not removed.")


if __name__ == "__main__":
    main()
