from unittest.mock import patch

from pytimings.tools import generate_example_data


def test_generate_example_data_creates_correct_number_of_files():
    with (
        patch("pytimings.timer.Timings") as MockTimings,  # noqa: N806
        patch("pytimings.timer.scoped_timing"),
        patch("pytimings.tools.busywait"),
    ):
        mock_timings = MockTimings.return_value
        mock_timings.output_files.return_value = "mock_file"
        files = generate_example_data("mock_output_dir", number_of_runs=5)
        assert len(files) == 4  # noqa: PLR2004


def test_generate_example_data_handles_zero_runs():
    with (
        patch("pytimings.timer.Timings") as MockTimings,  # noqa: N806
        patch("pytimings.timer.scoped_timing"),
        patch("pytimings.tools.busywait"),
    ):
        mock_timings = MockTimings.return_value
        mock_timings.output_files.return_value = "mock_file"
        files = generate_example_data("mock_output_dir", number_of_runs=0)
        assert len(files) == 0


def test_generate_example_data_creates_files_with_correct_names():
    with (
        patch("pytimings.timer.Timings") as MockTimings,  # noqa: N806
        patch("pytimings.timer.scoped_timing"),
        patch("pytimings.tools.busywait"),
    ):
        mock_timings = MockTimings.return_value
        mock_timings.output_files.side_effect = lambda output_dir, csv_base: f"{csv_base}.csv"
        files = generate_example_data("mock_output_dir", number_of_runs=3)
        assert files == ["example_speedup_00001.csv", "example_speedup_00002.csv"]


def test_generate_example_data_handles_large_number_of_runs():
    with (
        patch("pytimings.timer.Timings") as MockTimings,  # noqa: N806
        patch("pytimings.timer.scoped_timing"),
        patch("pytimings.tools.busywait"),
    ):
        mock_timings = MockTimings.return_value
        mock_timings.output_files.return_value = "mock_file"
        files = generate_example_data("mock_output_dir", number_of_runs=100)
        assert len(files) == 99  # noqa: PLR2004
