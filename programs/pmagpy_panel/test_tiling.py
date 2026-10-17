"""The tiling layout: panels always fill the area, and every move keeps them doing so."""
import itertools

import pytest

from pmagpy_panel import tiling

TREE = ["row", 0.5, "Z", ["row", 0.5, ["col", 0.62, "E", "D"], "L"]]


def assert_tiles(tree, w=1000, h=540, gap=8):
    """The panels cover the area exactly: inside it, no overlaps, area = total minus the gaps."""
    rects, dividers = tiling.layout(tree, w, h, gap)
    assert sorted(rects) == sorted(tiling.leaves(tree))
    for x, y, rw, rh in rects.values():
        assert x >= 0 and y >= 0 and x + rw <= w + 1 and y + rh <= h + 1 and rw > 0 and rh > 0
    for (a, ra), (b, rb) in itertools.combinations(rects.items(), 2):
        overlap_w = min(ra[0] + ra[2], rb[0] + rb[2]) - max(ra[0], rb[0])
        overlap_h = min(ra[1] + ra[3], rb[1] + rb[3]) - max(ra[1], rb[1])
        assert overlap_w <= 1 or overlap_h <= 1, (a, b)
    gaps = sum(d["w"] * d["h"] for d in dividers)
    assert abs(sum(r[2] * r[3] for r in rects.values()) + gaps - w * h) < 0.02 * w * h
    return rects, dividers


def test_the_default_layout_tiles_the_area():
    rects, dividers = assert_tiles(TREE)
    assert rects["Z"][:2] == (0, 0) and rects["Z"][3] == 540           # the diagram takes the full height
    assert rects["E"][1] == 0 and rects["D"][1] > rects["E"][1]          # the net over the M/M₀ curve
    assert len(dividers) == 3


@pytest.mark.parametrize("side", tiling.SIDES)
def test_moving_a_panel_to_each_side_of_another(side):
    tree = tiling.move(TREE, "D", "Z", side)
    rects, _ = assert_tiles(tree)
    d, z = rects["D"], rects["Z"]
    where = {"left": d[0] < z[0], "right": d[0] > z[0], "top": d[1] < z[1], "bottom": d[1] > z[1]}
    assert where[side]
    assert rects["E"][3] == 540                                          # D's place went to its sibling


def test_swap_and_impossible_moves():
    swapped = tiling.swap(TREE, "Z", "L")
    rects, _ = assert_tiles(swapped)
    before, _ = tiling.layout(TREE, 1000, 540)
    assert rects["L"] == before["Z"] and rects["Z"] == before["L"]
    assert tiling.move(TREE, "Z", "Z", "left") == TREE
    assert tiling.move(TREE, "Z", "nope", "left") == TREE
    assert tiling.move(TREE, "Z", "E", "middle") == TREE


def test_dividers_move_within_limits():
    tree = tiling.set_ratio(TREE, [], 0.7)
    rects, dividers = assert_tiles(tree)
    assert abs(rects["Z"][2] - 0.7 * 992) <= 1
    assert tiling.set_ratio(TREE, [], 5)[1] == tiling.MAX_RATIO
    assert tiling.set_ratio(TREE, [1, 0], 0.01, minimum=0.2)[3][2][1] == 0.2
    root = next(d for d in dividers if d["path"] == [])
    assert root["orient"] == "row" and root["x"] == rects["Z"][2]


def test_a_saved_layout_must_hold_the_same_panels():
    assert tiling.valid(TREE, "ZEDL")
    assert not tiling.valid(TREE, "ZED")
    assert not tiling.valid(["row", 1.5, "Z", "E"], "ZE")
    assert not tiling.valid(["diag", 0.5, "Z", "E"], "ZE")
    assert not tiling.valid(None, "ZE") and not tiling.valid({"a": 1}, "ZE")


def test_every_sequence_of_moves_keeps_the_area_tiled():
    tree, titles = TREE, "ZEDL"
    for src, dst in itertools.permutations(titles, 2):
        for side in tiling.SIDES:
            tree = tiling.move(tree, src, dst, side)
            assert_tiles(tree, 900, 600)
        tree = tiling.swap(tree, src, dst)
    assert sorted(tiling.leaves(tree)) == sorted(titles)


def test_no_panel_is_left_smaller_than_the_minimum():
    # the diagram dropped beside the narrow net: the split above makes room for both
    tree = tiling.move(TREE, "Z", "E", "left")
    tree = tiling.fit_minimum(tree, 1000, 540, 140)
    rects, _ = assert_tiles(tree)
    assert min(min(r[2], r[3]) for r in rects.values()) >= 139
    assert tiling.fit_minimum(TREE, 1000, 540, 140) == TREE              # nothing to do: unchanged
    tiny = tiling.fit_minimum(TREE, 300, 200, 140)                       # too small for all: shared out
    assert_tiles(tiny, 300, 200)
