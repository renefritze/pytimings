#!/usr/bin/env python3
from __future__ import annotations

import colorsys

__all__ = [
    "contrast_ratio",
    "discrete_cmap",
    "get_colour_palette",
    "get_colour_palette_cheat",
    "get_hue_vector",
    "get_hue_vector_rec",
]


def get_hue_vector(amount):
    level = 0
    while (1 << level) < amount:
        level += 1

    out = []
    return get_hue_vector_rec(out, amount, level)


def get_hue_vector_rec(out, amount, level):
    if level <= 1:
        if len(out) < amount:
            out.append(0.0)
        if len(out) < amount:
            out.append(0.5)
        return out
    else:
        out = get_hue_vector_rec(out, amount, level - 1)
        lower = len(out)
        out = get_hue_vector_rec(out, amount, level - 1)
        upper = len(out)
        for i in range(lower, upper):
            out[i] += 1.0 / (1 << level)
        return out


def get_colour_palette(size):
    result = []  # colors
    satvalbifurcatepos = 0
    satvalsplittings = []  # doubles
    if len(satvalsplittings) == 0:
        # // insert ranges to bifurcate
        satvalsplittings.append(1)
        satvalsplittings.append(0)
        satvalbifurcatepos = 0

    huevector = get_hue_vector(size)
    bisectionlimit = 20
    for i in range(len(result), size):
        hue = huevector[i]
        saturation = 1
        value = 1
        switccolors = i % 3  # ; // why only 3 and not all combinations? because it's easy, plus the bisection limit
        # cannot be divided integer by it

        if i % bisectionlimit == 0:
            satvalbifurcatepos = satvalbifurcatepos % (len(satvalsplittings) - 1)
            toinsert = satvalbifurcatepos + 1
            satvalsplittings.insert(
                toinsert,
                (satvalsplittings[satvalbifurcatepos] - satvalsplittings[satvalbifurcatepos + 1]) / 2
                + satvalsplittings[satvalbifurcatepos + 1],
            )
            satvalbifurcatepos += 2

        if switccolors == 1:
            saturation = satvalsplittings[satvalbifurcatepos - 1]
        elif switccolors == 2:  # noqa: PLR2004
            value = satvalsplittings[satvalbifurcatepos - 1]

        hue += 0.17  # ; // use as starting point a zone where color band is narrow so that small variations means
        # high change in visual effect
        if hue > 1:
            hue -= 1

        col = colorsys.hsv_to_rgb(hue, saturation, value)
        result.append(col)
    return result


def contrast_ratio(color_a, color_b):
    """Directional WCAG-style contrast ratio of two RGB colors with channels in [0, 1]."""

    def _lum(c):
        c = float(c)
        if c <= 0.03928:  # noqa: PLR2004
            return c / 12.92
        return ((c + 0.055) / 1.055) ** 2.4

    def _rel(rgb):
        return 0.2126 * _lum(rgb[0]) + 0.7152 * _lum(rgb[1]) + 0.0722 * _lum(rgb[2])

    return (_rel(color_a) + 0.05) / (_rel(color_b) + 0.05)


def get_colour_palette_cheat(size, filter_colors=None, bg_color=(1, 1, 1)):
    filter_colors = filter_colors or []
    target_len = size
    candidate_size = size
    max_size = size + 1000  # guard against impossible filters (e.g. a dark bg_color)
    k = []
    while len(k) < target_len:
        k = [
            p
            for p in set(get_colour_palette(candidate_size))
            if p not in filter_colors and contrast_ratio(p, bg_color) < 0.6  # noqa: PLR2004
        ]
        candidate_size += 1
        if candidate_size > max_size:
            raise RuntimeError(
                f"could not find {target_len} colors with sufficient contrast against bg_color={bg_color}"
            )
    return k[:target_len]


def discrete_cmap(count, bg_color=(255, 255, 255), name="indexed"):
    import matplotlib as mpl

    cmap = mpl.colors.ListedColormap(get_colour_palette_cheat(count, bg_color=bg_color), name)
    mpl.colormaps.register(cmap=cmap)
    return cmap


if __name__ == "__main__":
    print(get_colour_palette(4))
    print(get_colour_palette_cheat(4))
    print(get_colour_palette_cheat(4, [(0.0, 0, 0.0)]))
