from context_graph_builder.tarball_ingestion import _find_package_root


def test_find_package_root_locates_valid_package(tmp_path):
    pkg_dir = tmp_path / "SomeDist-1.0" / "somepkg"
    pkg_dir.mkdir(parents=True)
    (pkg_dir / "__init__.py").write_text("")

    result = _find_package_root(tmp_path, "somepkg")

    assert result == pkg_dir


def test_find_package_root_returns_none_when_missing(tmp_path):
    result = _find_package_root(tmp_path, "nonexistent")
    assert result is None