#!/usr/bin/env python3

import matplotlib as mpl


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
        import colorsys

        col = colorsys.hsv_to_rgb(hue, saturation, value)
        result.append(col)
    return result


def contrast_ratio(color_a, color_b):
    def _lum(c):
        index = float(c) * 255
        if index < 0.03928:  # noqa: PLR2004
            return index / 12.92
        else:
            return ((index + 0.055) / 1.055) ** 2.4

    def _rel(rgb):
        return 0.2126 * _lum(rgb[0]) + 0.7152 * _lum(rgb[1]) + 0.0722 * _lum(rgb[2])

    return (_rel(color_a) + 0.05) / (_rel(color_b) + 0.05)


def get_colour_palette_cheat(size, filter_colors=None, bg_color=(1, 1, 1)):
    filter_colors = filter_colors or []
    k = []
    target_len = size
    while len(k) < target_len:
        k = [
            p
            for p in set(get_colour_palette(size))
            if p not in filter_colors and contrast_ratio(p, bg_color) < 0.6  # noqa: PLR2004
        ]
        size += 1
    for p in k:
        print(f"{p} ratio: {contrast_ratio(p, bg_color)}")
    return k


def discrete_cmap(count, bg_color=(255, 255, 255), name="indexed"):
    cmap = mpl.colors.ListedColormap(get_colour_palette_cheat(count, bg_color=bg_color), name)
    mpl.colormaps.register(cmap=cmap)
    return cmap


if __name__ == "__main__":
    # k = getColourPalette( 9 )
    # print k
    # k = set(k)
    # print k
    print(get_colour_palette(4))
    print(get_colour_palette_cheat(4))
    print(get_colour_palette_cheat(4, [(0.0, 0, 0.0)]))
