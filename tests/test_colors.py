import matplotlib
import pytest

from pytimings.plotting.colors import (
    _MAX_CONTRAST_RATIO,
    contrast_ratio,
    discrete_cmap,
    get_colour_palette,
    get_colour_palette_cheat,
    get_hue_vector_rec,
)


@pytest.fixture(scope="function")
def cmap_name():
    name = "indexed"
    yield name
    matplotlib.colormaps.unregister(name)


def test_discrete_cmap_creates_correct_number_of_colors(cmap_name):
    count = 5
    cmap = discrete_cmap(count, name=cmap_name)
    assert len(cmap.colors) == count


def test_discrete_cmap_handles_zero_colors(cmap_name):
    cmap = discrete_cmap(0, name=cmap_name)
    assert len(cmap.colors) == 0


def test_discrete_cmap_uses_default_bg_color(cmap_name):
    cmap = discrete_cmap(3, name=cmap_name)
    assert cmap.colors[0] != (255, 255, 255)


def test_discrete_cmap_rejects_dark_bg_color():
    # against a dark background the directional contrast filter can never be satisfied,
    # so the palette generator gives up instead of looping forever
    with pytest.raises(RuntimeError):
        discrete_cmap(3, bg_color=(0, 0, 0))


def test_get_colour_palette_cheat_creates_correct_number_of_colors():
    count = 5
    palette = get_colour_palette_cheat(count)
    assert len(palette) == count


def test_get_colour_palette_cheat_handles_zero_colors():
    palette = get_colour_palette_cheat(0)
    assert len(palette) == 0


def test_get_colour_palette_cheat_excludes_filter_colors():
    filter_colors = [(1, 0, 0), (0, 1, 0)]
    palette = get_colour_palette_cheat(5, filter_colors=filter_colors)
    for color in filter_colors:
        assert color not in palette


def test_get_colour_palette_cheat_uses_default_bg_color():
    palette = get_colour_palette_cheat(3)
    for color in palette:
        assert contrast_ratio(color, (1, 1, 1)) < _MAX_CONTRAST_RATIO


def test_get_colour_palette_cheat_rejects_dark_bg_color():
    with pytest.raises(RuntimeError):
        get_colour_palette_cheat(3, bg_color=(0, 0, 0))


def test_contrast_ratio_identical_colors():
    assert contrast_ratio((1, 1, 1), (1, 1, 1)) == 1.05 / 1.05


def test_contrast_ratio_black_and_white():
    assert contrast_ratio((0, 0, 0), (1, 1, 1)) == pytest.approx(0.05 / 1.05)


def test_contrast_ratio_color_and_black():
    assert contrast_ratio((0.5, 0.5, 0.5), (0, 0, 0)) > 1


def test_contrast_ratio_color_and_white():
    assert contrast_ratio((0.5, 0.5, 0.5), (1, 1, 1)) < 1


def test_contrast_ratio_handles_low_luminance():
    # very small channel values exercise the linear (c / 12.92) branch and stay finite
    ratio = contrast_ratio((0.01, 0.01, 0.01), (0.02, 0.02, 0.02))
    assert 0 < ratio < 1


def test_get_colour_palette_creates_correct_number_of_colors():
    count = 5
    palette = get_colour_palette(count)
    assert len(palette) == count


def test_get_colour_palette_handles_zero_colors():
    palette = get_colour_palette(0)
    assert len(palette) == 0


def test_get_colour_palette_uses_correct_hue_values():
    palette = get_colour_palette(3)
    assert all(0 <= color[0] <= 1 for color in palette)


def test_get_colour_palette_returns_valid_rgb_components():
    # get_colour_palette returns RGB tuples; every channel must lie within [0, 1]
    palette = get_colour_palette(3)
    assert all(all(0 <= channel <= 1 for channel in color) for color in palette)


def test_get_colour_palette_handles_large_number_of_colors():
    size = 100
    palette = get_colour_palette(size)
    assert len(palette) == size


def test_get_hue_vector_rec_creates_correct_hue_vector():
    out = []
    result = get_hue_vector_rec(out, 4, 2)
    assert result == [0.0, 0.5, 0.25, 0.75]


def test_get_hue_vector_rec_handles_single_level():
    out = []
    result = get_hue_vector_rec(out, 2, 1)
    assert result == [0.0, 0.5]


def test_get_hue_vector_rec_handles_zero_amount():
    out = []
    result = get_hue_vector_rec(out, 0, 1)
    assert result == []


def test_get_hue_vector_rec_handles_large_amount():
    out = []
    result = get_hue_vector_rec(out, 8, 3)
    assert result == [0.0, 0.5, 0.25, 0.75, 0.125, 0.625, 0.375, 0.875]


def test_get_hue_vector_rec_handles_non_power_of_two_amount():
    out = []
    result = get_hue_vector_rec(out, 3, 2)
    assert result == [0.0, 0.5, 0.25]
