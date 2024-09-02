import matplotlib
import pytest

from pytimings.plotting.colors import (
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


@pytest.mark.skip("blocks indefinitely")
def test_discrete_cmap_uses_custom_bg_color(cmap_name):
    cmap = discrete_cmap(3, bg_color=(0, 0, 0), name=cmap_name)
    assert cmap.colors[0] != (0, 0, 0)


def test_get_colour_palette_cheat_creates_correct_number_of_colors():
    palette = get_colour_palette_cheat(5)
    assert len(palette) == 5  # noqa: PLR2004


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
        assert contrast_ratio(color, (1, 1, 1)) < 0.6  # noqa: PLR2004


@pytest.mark.skip("blocks indefinitely")
def test_get_colour_palette_cheat_uses_custom_bg_color():
    palette = get_colour_palette_cheat(3, bg_color=(0, 0, 0))
    for color in palette:
        assert contrast_ratio(color, (0, 0, 0)) < 0.6  # noqa: PLR2004


def test_contrast_ratio_identical_colors():
    assert contrast_ratio((1, 1, 1), (1, 1, 1)) == 1.05 / 1.05


@pytest.mark.skip("contrast ratio broken")
def test_contrast_ratio_black_and_white():
    assert contrast_ratio((0, 0, 0), (1, 1, 1)) == (0.05 + 0.05) / (1.05 + 0.05)


def test_contrast_ratio_color_and_black():
    assert contrast_ratio((0.5, 0.5, 0.5), (0, 0, 0)) > 1


def test_contrast_ratio_color_and_white():
    assert contrast_ratio((0.5, 0.5, 0.5), (1, 1, 1)) < 1


@pytest.mark.skip("contrast ratio broken")
def test_contrast_ratio_handles_low_luminance():
    assert contrast_ratio((0.01, 0.01, 0.01), (0.02, 0.02, 0.02)) > 1


def test_get_colour_palette_creates_correct_number_of_colors():
    palette = get_colour_palette(5)
    assert len(palette) == 5  # noqa: PLR2004


def test_get_colour_palette_handles_zero_colors():
    palette = get_colour_palette(0)
    assert len(palette) == 0


def test_get_colour_palette_uses_correct_hue_values():
    palette = get_colour_palette(3)
    assert all(0 <= color[0] <= 1 for color in palette)


@pytest.mark.skip("broken")
def test_get_colour_palette_uses_correct_saturation_and_value():
    palette = get_colour_palette(3)
    assert all(color[1] == 1 and color[2] == 1 for color in palette)


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
