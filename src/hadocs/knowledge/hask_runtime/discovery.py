from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


def packaged_bundle_path() -> Path:
    """Return the immutable bundle installed with the HADocs package."""

    return Path(__file__).resolve().parents[1] / "hask_bundle" / "0.2.1"


@dataclass(frozen=True, slots=True)
class DiscoveryResult:
    path: Path | None
    source: str
    status: str


class BundleDiscovery:
    """Discover local bundles only; never performs network I/O."""

    def __init__(
        self,
        standard_paths: tuple[Path, ...] | None = None,
        packaged_path: Path | None = None,
    ) -> None:
        self.standard_paths = standard_paths or self._defaults()
        self.packaged_path = (
            packaged_path
            if packaged_path is not None
            else (None if standard_paths is not None else packaged_bundle_path())
        )

    @staticmethod
    def _defaults() -> tuple[Path, ...]:
        from hadocs.platform.paths import AppPaths

        paths = []
        program_data = os.getenv("PROGRAMDATA")
        if program_data:
            paths.append(Path(program_data) / "HADocs" / "knowledge" / "hask")
        paths.append(Path.home() / ".local" / "share" / "hadocs" / "hask")
        paths.append(AppPaths.discover().resolve_resource_path("knowledge/hask"))
        return tuple(paths)

    def discover(self, configured: Path | None = None) -> DiscoveryResult:
        if configured is not None:
            path = configured.expanduser().resolve()
            return DiscoveryResult(path if path.is_dir() else None, "configured", "found" if path.is_dir() else "missing")
        if self.packaged_path is not None:
            path = self.packaged_path.resolve()
            if path.is_dir() and (path / "manifest.json").is_file():
                return DiscoveryResult(path, "packaged", "found")
        for candidate in self.standard_paths:
            path = candidate.expanduser().resolve()
            if path.is_dir() and (path / "manifest.json").is_file():
                return DiscoveryResult(path, "standard", "found")
        return DiscoveryResult(None, "standard", "missing")
