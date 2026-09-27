"""Тесты для tools/files.py — read_file, write_file."""
import pytest

from tools.files import read_file, write_file


class TestWriteFile:

    @pytest.mark.unit
    def test_write_new(self, temp_dir):
        path = temp_dir / "test.txt"
        result = write_file(str(path), "hello")
        assert "[OK]" in result
        assert path.read_text(encoding="utf-8") == "hello"

    @pytest.mark.unit
    def test_write_overwrite(self, temp_dir):
        path = temp_dir / "test.txt"
        write_file(str(path), "first")
        write_file(str(path), "second")
        assert path.read_text(encoding="utf-8") == "second"

    @pytest.mark.unit
    def test_write_creates_parent_dir(self, temp_dir):
        path = temp_dir / "sub" / "dir" / "test.txt"
        result = write_file(str(path), "hello")
        assert "[OK]" in result
        assert path.exists()

    @pytest.mark.unit
    def test_write_unicode(self, temp_dir):
        path = temp_dir / "test.txt"
        write_file(str(path), "привет мир 🌍")
        assert path.read_text(encoding="utf-8") == "привет мир 🌍"


class TestReadFile:

    @pytest.mark.unit
    def test_read_existing(self, temp_dir):
        path = temp_dir / "test.txt"
        path.write_text("hello world", encoding="utf-8")
        assert read_file(str(path)) == "hello world"

    @pytest.mark.unit
    def test_read_missing(self, temp_dir):
        result = read_file(str(temp_dir / "missing.txt"))
        assert "[ERROR]" in result

    @pytest.mark.unit
    def test_read_unicode(self, temp_dir):
        path = temp_dir / "test.txt"
        path.write_text("привет мир", encoding="utf-8")
        assert read_file(str(path)) == "привет мир"

    @pytest.mark.unit
    def test_read_directory(self, temp_dir):
        result = read_file(str(temp_dir))
        assert "[ERROR]" in result

    @pytest.mark.unit
    def test_read_large_file_truncated(self, temp_dir):
        path = temp_dir / "big.txt"
        path.write_text("x" * 20000, encoding="utf-8")
        result = read_file(str(path))
        assert "обрезано" in result.lower()
        assert len(result) < 20000


class TestRoundTrip:

    @pytest.mark.unit
    def test_write_read_roundtrip(self, temp_dir):
        path = temp_dir / "test.txt"
        content = "line1\nline2\nline3"
        write_file(str(path), content)
        assert read_file(str(path)) == content