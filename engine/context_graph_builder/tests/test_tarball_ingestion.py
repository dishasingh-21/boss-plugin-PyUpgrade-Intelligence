from context_graph_builder.tarball_ingestion import _find_package_root


def test_exact_name_match_flat_layout(tmp_path):
    pkg_dir = tmp_path / "SomeDist-1.0" / "somepkg"
    pkg_dir.mkdir(parents=True)
    (pkg_dir / "__init__.py").write_text("")
    assert _find_package_root(tmp_path, "somepkg") == pkg_dir


def test_hyphen_underscore_variant_matched_directly(tmp_path):
    pkg_dir = tmp_path / "my-package-1.0" / "my_package"
    pkg_dir.mkdir(parents=True)
    (pkg_dir / "__init__.py").write_text("")
    assert _find_package_root(tmp_path, "my-package") == pkg_dir


def test_src_layout_matched_by_general_search(tmp_path):
    pkg_dir = tmp_path / "SomeDist-2.0" / "src" / "somepkg"
    pkg_dir.mkdir(parents=True)
    (pkg_dir / "__init__.py").write_text("")
    assert _find_package_root(tmp_path, "somepkg") == pkg_dir


def test_sole_directory_fallback_matches_livekit_style(tmp_path):
    sdist_root = tmp_path / "livekit_agents-1.5.1"
    pkg_dir = sdist_root / "livekit"
    (pkg_dir / "agents").mkdir(parents=True)
    (pkg_dir / "agents" / "__init__.py").write_text("")
    (sdist_root / "PKG-INFO").write_text("")
    (sdist_root / "pyproject.toml").write_text("")
    (sdist_root / "README.md").write_text("")
    assert _find_package_root(tmp_path, "livekit_agents") == pkg_dir


def test_sole_directory_fallback_matches_pillow_style(tmp_path):
    """Same class of exception as livekit: PyPI 'pillow' vs import 'PIL'."""
    sdist_root = tmp_path / "Pillow-10.0.0"
    pkg_dir = sdist_root / "PIL"
    pkg_dir.mkdir(parents=True)
    (pkg_dir / "__init__.py").write_text("")
    (sdist_root / "setup.py").write_text("")
    assert _find_package_root(tmp_path, "pillow") == pkg_dir


def test_shallowest_match_preferred_over_deep_coincidence(tmp_path):
    sdist_root = tmp_path / "SomeDist-1.0"
    shallow_pkg = sdist_root / "somepkg"
    shallow_pkg.mkdir(parents=True)
    (shallow_pkg / "__init__.py").write_text("")
    (shallow_pkg / "vendor" / "somepkg").mkdir(parents=True)
    assert _find_package_root(tmp_path, "somepkg") == shallow_pkg


def test_ambiguous_layout_returns_none_not_a_guess(tmp_path):
    sdist_root = tmp_path / "Ambiguous-1.0"
    (sdist_root / "pkg_one").mkdir(parents=True)
    (sdist_root / "pkg_one" / "__init__.py").write_text("")
    (sdist_root / "pkg_two").mkdir()
    (sdist_root / "pkg_two" / "__init__.py").write_text("")
    assert _find_package_root(tmp_path, "nonmatching_name") is None


def test_test_and_docs_dirs_excluded_from_fallback(tmp_path):
    sdist_root = tmp_path / "SomeDist-1.0"
    pkg_dir = sdist_root / "realpkg"
    pkg_dir.mkdir(parents=True)
    (pkg_dir / "__init__.py").write_text("")
    (sdist_root / "tests").mkdir()
    (sdist_root / "docs").mkdir()
    assert _find_package_root(tmp_path, "nonmatching_name") == pkg_dir