"""
Tiling of panels in a fixed area, after the manner of a tiling window manager
(Hyprland's *dwindle* layout, as Omarchy uses it).

The layout is a binary tree: a leaf is a panel's title, a node splits its area
in two side by side (``"row"``) or one above the other (``"col"``) at a ratio.
The panels therefore always fill the area exactly — no gaps, no overlaps,
nothing pushed out of it — and every rearrangement is one of three moves on
the tree:

* :func:`swap` two panels (a panel dropped on the middle of another);
* :func:`move` a panel to one side of another (dropped near that edge): it
  leaves its place, its sibling takes the whole of it, and the target's area
  is split between the target and the panel;
* :func:`set_ratio` of a split (its divider dragged).

A tree is plain JSON — ``["row", 0.5, "A", ["col", 0.6, "B", "C"]]`` — so it
can be saved and restored as it is. Pure Python, no Panel: the browser
component (:class:`pmagpy_panel.widgets.TileCanvas`) only draws what
:func:`layout` computes and reports the analyst's drags.
"""
from __future__ import annotations

from typing import Optional, Union

Tree = Union[str, list]

SIDES = ("left", "right", "top", "bottom")
MIN_RATIO, MAX_RATIO = 0.08, 0.92


def is_leaf(tree: Tree) -> bool:
    return isinstance(tree, str)


def leaves(tree: Tree) -> list[str]:
    """The panels of a layout, in reading order."""
    if is_leaf(tree):
        return [tree]
    return leaves(tree[2]) + leaves(tree[3])


def valid(tree, titles) -> bool:
    """True when ``tree`` is a well-formed layout of exactly ``titles``."""
    def ok(node):
        if is_leaf(node):
            return True
        return (isinstance(node, list) and len(node) == 4 and node[0] in ("row", "col")
                and isinstance(node[1], (int, float)) and 0 < node[1] < 1 and ok(node[2]) and ok(node[3]))
    try:
        return ok(tree) and sorted(leaves(tree)) == sorted(titles)
    except (TypeError, IndexError):
        return False


def layout(tree: Tree, width: float, height: float, gap: float = 8.0):
    """Where every panel goes in a ``width`` x ``height`` area, and where the dividers are.

    Returns:
        (rects, dividers): ``rects`` maps each title to ``(x, y, w, h)`` in
        pixels (whole numbers, the area's top-left at 0, 0); each divider is a
        dict with the ``path`` of its split (0/1 steps from the root), its
        ``orient`` (``"row"``: a vertical bar between side-by-side panels), its
        own box ``x, y, w, h`` (the gap between the two sides), and ``start``,
        ``length`` -- the extent of the split along its axis -- from which the
        browser turns a drop position into a ratio.
    """
    rects, dividers = {}, []

    def place(node, x, y, w, h, path):
        if is_leaf(node):
            rects[node] = (int(round(x)), int(round(y)), int(round(w)), int(round(h)))
            return
        kind, ratio, a, b = node
        if kind == "row":
            wa = max(0.0, (w - gap) * ratio)
            place(a, x, y, wa, h, path + [0])
            place(b, x + wa + gap, y, w - wa - gap, h, path + [1])
            dividers.append(dict(path=path, orient="row", x=round(x + wa), y=round(y), w=gap, h=round(h),
                                 start=round(x), length=round(w)))
        else:
            ha = max(0.0, (h - gap) * ratio)
            place(a, x, y, w, ha, path + [0])
            place(b, x, y + ha + gap, w, h - ha - gap, path + [1])
            dividers.append(dict(path=path, orient="col", x=round(x), y=round(y + ha), w=round(w), h=gap,
                                 start=round(y), length=round(h)))

    place(tree, 0.0, 0.0, float(width), float(height), [])
    return rects, dividers


def swap(tree: Tree, a: str, b: str) -> Tree:
    """The layout with panels ``a`` and ``b`` exchanged."""
    if is_leaf(tree):
        return b if tree == a else a if tree == b else tree
    return [tree[0], tree[1], swap(tree[2], a, b), swap(tree[3], a, b)]


def remove(tree: Tree, title: str) -> Optional[Tree]:
    """The layout without ``title``: its sibling takes the whole of their area (None if it was alone)."""
    if is_leaf(tree):
        return None if tree == title else tree
    kind, ratio, a, b = tree
    if a == title:
        return b
    if b == title:
        return a
    return [kind, ratio, remove(a, title), remove(b, title)]


def _split_leaf(tree: Tree, target: str, title: str, side: str) -> Tree:
    if is_leaf(tree):
        if tree != target:
            return tree
        kind = "row" if side in ("left", "right") else "col"
        first = side in ("left", "top")
        return [kind, 0.5, title, target] if first else [kind, 0.5, target, title]
    return [tree[0], tree[1], _split_leaf(tree[2], target, title, side), _split_leaf(tree[3], target, title, side)]


def move(tree: Tree, title: str, target: str, side: str) -> Tree:
    """Put ``title`` on ``side`` ("left", "right", "top", "bottom") of ``target``, which gives up half its area."""
    if title == target or side not in SIDES or title not in leaves(tree) or target not in leaves(tree):
        return tree
    rest = remove(tree, title)
    return _split_leaf(rest, target, title, side)


def node_at(tree: Tree, path) -> Tree:
    for step in path:
        tree = tree[2 + int(step)]
    return tree


def set_ratio(tree: Tree, path, ratio: float, minimum: float = MIN_RATIO) -> Tree:
    """The layout with the split at ``path`` moved to ``ratio`` (kept within [minimum, 1 - minimum])."""
    minimum = min(max(minimum, MIN_RATIO), 0.5)
    ratio = min(max(float(ratio), minimum), 1.0 - minimum)

    def walk(node, rest):
        if is_leaf(node):
            return node
        if not rest:
            return [node[0], ratio, node[2], node[3]]
        i = int(rest[0])
        children = [node[2], node[3]]
        children[i] = walk(children[i], rest[1:])
        return [node[0], node[1]] + children

    return walk(tree, list(path))


def need(tree: Tree, minimum: float, gap: float) -> tuple[float, float]:
    """The smallest (width, height) a layout fits in with every panel at least ``minimum`` square."""
    if is_leaf(tree):
        return float(minimum), float(minimum)
    kind, _, a, b = tree
    (wa, ha), (wb, hb) = need(a, minimum, gap), need(b, minimum, gap)
    if kind == "row":
        return wa + gap + wb, max(ha, hb)
    return max(wa, wb), ha + gap + hb


def fit_minimum(tree: Tree, width: float, height: float, minimum: float, gap: float = 8.0) -> Tree:
    """The layout with every split moved just enough that no panel is smaller than ``minimum``.

    Each split, from the root down, keeps its ratio unless a side would get less
    than its own panels need; a panel dropped into a small corner therefore takes
    its room from the larger panels around it. Where the area is too small for
    all of them, each side gets its share in proportion to what it needs.
    """
    if is_leaf(tree):
        return tree
    kind, ratio, a, b = tree
    extent, other = (width, height) if kind == "row" else (height, width)
    avail = max(extent - gap, 1.0)
    axis = 0 if kind == "row" else 1
    lo, rest = need(a, minimum, gap)[axis], need(b, minimum, gap)[axis]
    size_a = ratio * avail
    if lo + rest <= avail:
        size_a = min(max(size_a, lo), avail - rest)
    else:
        size_a = avail * lo / (lo + rest)
    new_ratio = min(max(size_a / avail, 0.02), 0.98)
    if kind == "row":
        return [kind, new_ratio, fit_minimum(a, size_a, height, minimum, gap),
                fit_minimum(b, avail - size_a, height, minimum, gap)]
    return [kind, new_ratio, fit_minimum(a, width, size_a, minimum, gap),
            fit_minimum(b, width, avail - size_a, minimum, gap)]
