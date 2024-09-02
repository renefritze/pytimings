from unittest.mock import patch

import pytest

from pytimings.plotting.pad_rank_dir import pad_rank_dir


def test_pad_rank_dir_creates_correct_new_name():
    with patch("sys.argv", ["pad_rank_dir.py", "_n", "dir_n1"]):
        with patch("os.path.isdir", return_value=True):
            with patch("shutil.move") as mock_move:
                pad_rank_dir(["pad_rank_dir.py", "_n", "dir_n1"])
                mock_move.assert_called_with("dir_n1", "dir_n00000001")


def test_pad_rank_dir_handles_multiple_directories():
    with patch("sys.argv", ["pad_rank_dir.py", "_n", "dir_n1", "dir_n2"]):
        with patch("os.path.isdir", return_value=True):
            with patch("shutil.move") as mock_move:
                pad_rank_dir(["pad_rank_dir.py", "_n", "dir_n1", "dir_n2"])
                mock_move.assert_any_call("dir_n1", "dir_n00000001")
                mock_move.assert_any_call("dir_n2", "dir_n00000002")


def test_pad_rank_dir_handles_custom_marker():
    with patch("sys.argv", ["pad_rank_dir.py", ".01_", "dir.01_1"]):
        with patch("os.path.isdir", return_value=True):
            with patch("shutil.move") as mock_move:
                pad_rank_dir(["pad_rank_dir.py", ".01_", "dir.01_1"])
                mock_move.assert_called_with("dir.01_1", "dir.01_00000001")


def test_pad_rank_dir_handles_non_existent_directory():
    with patch("sys.argv", ["pad_rank_dir.py", "_n", "non_existent_dir"]):
        with patch("os.path.isdir", return_value=False):
            with pytest.raises(AssertionError):
                pad_rank_dir(["pad_rank_dir.py", "_n", "non_existent_dir"])


def test_pad_rank_dir_handles_no_directories():
    with patch("sys.argv", ["pad_rank_dir.py", "_n"]):
        with patch("shutil.move") as mock_move:
            pad_rank_dir(["pad_rank_dir.py", "_n"])
            mock_move.assert_not_called()
