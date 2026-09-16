# Fetches a framework's source code for a given version from PyPI, caching the extracted source on disk so a version is never downloaded or extracted more than once.

import io
import json
import tarfile
import urllib.request
from pathlib import Path

_NON_SOURCE_DIR_NAMES = {"tests", "test", "docs", "doc", "examples", "example", "benchmarks", "scripts", "ci", "build", "dist", ".github", ".circleci", ".git"}

def fetch_source(framework: str, version: str, cache_dir: str = "./framework_source_cache", package_name: str | None = None) -> Path:
    resolved_package_name = package_name or framework.lower()
    dest = Path(cache_dir) / f"{framework}_{version}"
    cached = _find_package_root(dest, resolved_package_name)
    if cached is not None:
        return cached

    dest.mkdir(parents=True, exist_ok=True)
    url = f"https://pypi.org/pypi/{framework}/{version}/json"
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read())

    sdist_url = next((f["url"] for f in data["urls"] if f["packagetype"] == "sdist"), None)
    if not sdist_url:
        raise RuntimeError(f"No source distribution found for {framework} {version}")
    with urllib.request.urlopen(sdist_url) as response:
        tar_bytes = response.read()
    with tarfile.open(fileobj=io.BytesIO(tar_bytes)) as tar:
        tar.extractall(path=dest, filter="data")

    package_root = _find_package_root(dest, resolved_package_name)
    if package_root is None:
        candidates = _list_plausible_source_dirs(dest)
        raise RuntimeError(
            f"Could not confidently locate the package for '{framework}' inside {dest}. "
            f"Candidates found: {candidates or 'none'}.\n"
            f"CLI: for e.g., Add --package <correct-package-name> at the end of the command\n"
            f"MCP tool: pass packageName: <correct-package-name>"
        )

    return package_root

def _find_package_root(dest: Path, package_name: str) -> Path | None:
    if not dest.exists():
        return None
    variants = _name_variants(package_name)
    name_matches = [d for d in dest.rglob("*") if d.is_dir() and d.name.lower() in variants and not _is_excluded_dir(d, dest)]
    if name_matches:
        name_matches.sort(key=lambda d: (len(d.relative_to(dest).parts), -_py_file_count(d)))
        return name_matches[0]
    sdist_roots = [d for d in dest.iterdir() if d.is_dir()]
    if len(sdist_roots) != 1:
        return None
    plausible = _plausible_dirs(sdist_roots[0])
    if len(plausible) == 1:
        return plausible[0]
    return None

def _name_variants(name: str) -> set[str]:
    lower = name.lower()
    return {lower, lower.replace("-", "_"), lower.replace("_", "-"), lower.replace("-", "").replace("_", "")}

def _is_excluded_dir(d: Path, dest: Path) -> bool:
    for part in d.relative_to(dest).parts:
        if part.startswith(".") or part.endswith(".egg-info"):
            return True
        if part.lower() in _NON_SOURCE_DIR_NAMES:
            return True

    return False

def _plausible_dirs(parent: Path) -> list[Path]:
    return [d for d in parent.iterdir() if d.is_dir() and not d.name.startswith(".") and not d.name.endswith(".egg-info") and d.name.lower() not in _NON_SOURCE_DIR_NAMES]

def _py_file_count(d: Path) -> int:
    try:
        return sum(1 for _ in d.rglob("*.py"))
    except OSError:
        return 0

def _list_plausible_source_dirs(dest: Path) -> list[str]:
    sdist_roots = [d for d in dest.iterdir() if d.is_dir()] if dest.exists() else []
    if len(sdist_roots) != 1:
        return []
    return [d.name for d in _plausible_dirs(sdist_roots[0])]