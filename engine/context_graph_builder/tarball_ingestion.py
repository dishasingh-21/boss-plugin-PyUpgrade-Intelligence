# Fetches a framework's source code for a given version from PyPI, caching the extracted source on disk so a version is never downloaded or extracted more than once.

import io
import json
import tarfile
import urllib.request
from pathlib import Path

def fetch_source(framework: str, version: str, cache_dir: str = "./framework_source_cache", package_name: str | None = None) -> Path:
    package_name = package_name or framework.lower()
    dest = Path(cache_dir) / f"{framework}_{version}"
    cached = _find_package_root(dest, package_name)
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

    package_root = _find_package_root(dest, package_name)
    if package_root is None:
        raise RuntimeError(f"Could not locate package '{package_name}' inside extracted source at {dest}")

    return package_root

def _find_package_root(dest: Path, package_name: str) -> Path | None:
    if not dest.exists():
        return None
    for candidate in dest.rglob(package_name):
        if candidate.is_dir() and (candidate / "__init__.py").exists():
            return candidate
    return None
