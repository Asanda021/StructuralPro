import pytest

from core.drawings.viewport_tools import ViewportRect


def test_viewport_rect_normalizes_reverse_drag_direction():
    rect = ViewportRect.from_points(90, 70, 10, 20)
    assert (rect.left, rect.top, rect.right, rect.bottom) == (10, 20, 90, 70)
    assert rect.width == 80
    assert rect.height == 50


def test_viewport_rect_rejects_click_sized_selection():
    assert not ViewportRect.from_points(10, 10, 15, 16).is_usable()
    assert ViewportRect.from_points(10, 10, 18, 18).is_usable()


def test_viewport_rect_clamps_to_scene_bounds():
    rect = ViewportRect.from_points(-5, 5, 20, 30).clamped(
        ViewportRect(0, 0, 10, 20)
    )
    assert rect == ViewportRect(0, 5, 10, 20)
    assert rect.area == 150


def test_viewport_rect_rejects_negative_minimum_size():
    with pytest.raises(ValueError):
        ViewportRect(0, 0, 10, 10).is_usable(-1)


@pytest.mark.parametrize("coordinates", [
    (float("nan"), 0, 100, 100),
    (0, float("inf"), 100, 100),
    (0, 0, float("-inf"), 100),
    (True, 0, 100, 100),
])
def test_zoom_selection_rejects_nonfinite_or_boolean_drag_coordinates(coordinates):
    with pytest.raises(ValueError, match="متناهی"):
        ViewportRect.from_points(*coordinates)


@pytest.mark.parametrize("size", [float("nan"), float("inf"), -1])
def test_zoom_rejects_invalid_minimum_size(size):
    with pytest.raises(ValueError, match="finite"):
        ViewportRect.from_points(0, 0, 100, 100).is_usable(size)


def test_zoom_clamp_rejects_nonfinite_bounds_instead_of_producing_invalid_scene_rect():
    rect = ViewportRect.from_points(0, 0, 100, 100)
    with pytest.raises(ValueError, match="متناهی"):
        rect.clamped(ViewportRect(0, 0, float("inf"), 100))
