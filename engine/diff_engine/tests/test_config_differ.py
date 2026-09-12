from diff_engine.config_differ import diff_config_files


def test_config_diff_detects_changed_file(tmp_path):
    old_dir, new_dir = tmp_path / "old", tmp_path / "new"
    old_dir.mkdir(); new_dir.mkdir()
    (old_dir / "pyproject.toml").write_text("python = '>=3.8'\n")
    (new_dir / "pyproject.toml").write_text("python = '>=3.10'\n")
    result = diff_config_files(str(old_dir), str(new_dir))
    assert "pyproject.toml" in result
    assert "3.10" in result["pyproject.toml"]


def test_config_diff_ignores_identical_files(tmp_path):
    old_dir, new_dir = tmp_path / "old", tmp_path / "new"
    old_dir.mkdir(); new_dir.mkdir()
    (old_dir / "setup.cfg").write_text("[metadata]\nname = foo\n")
    (new_dir / "setup.cfg").write_text("[metadata]\nname = foo\n")
    result = diff_config_files(str(old_dir), str(new_dir))
    assert result == {}


def test_config_diff_handles_missing_file_gracefully(tmp_path):
    old_dir, new_dir = tmp_path / "old", tmp_path / "new"
    old_dir.mkdir(); new_dir.mkdir()
    (new_dir / "requirements.txt").write_text("django>=5.0\n")
    result = diff_config_files(str(old_dir), str(new_dir))
    assert "requirements.txt" in result