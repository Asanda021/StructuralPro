import math
import pytest

from core.drawings.graphical_takeoff import MeasurementStore, Point, ScaleCalibration, polygon_area, polyline_length, subtract_areas, snap_point


@pytest.mark.parametrize("ratio", [0, -1, math.nan, math.inf, -math.inf, True])
def test_scale_calibration_rejects_invalid_ratios(ratio):
    with pytest.raises(ValueError):
        ScaleCalibration.parse(ratio)


@pytest.mark.parametrize("distance", [-1, math.nan, math.inf, -math.inf])
def test_scale_calibration_rejects_invalid_lengths(distance):
    with pytest.raises(ValueError):
        ScaleCalibration.parse(100).length(distance)


@pytest.mark.parametrize("area", [-1, math.nan, math.inf, -math.inf])
def test_scale_calibration_rejects_invalid_areas(area):
    with pytest.raises(ValueError):
        ScaleCalibration.parse(100).area(area)


@pytest.mark.parametrize("points", [
    [Point(0, 0), Point(math.nan, 1)],
    [Point(0, 0), Point(math.inf, 1)],
])
def test_polyline_rejects_non_finite_coordinates(points):
    with pytest.raises(ValueError):
        polyline_length(points)


def test_polygon_area_rejects_non_finite_coordinates():
    with pytest.raises(ValueError):
        polygon_area([Point(0, 0), Point(1, 0), Point(math.nan, 1)])


@pytest.mark.parametrize("holes", [[-1], [math.nan], [math.inf]])
def test_area_subtraction_rejects_invalid_openings(holes):
    with pytest.raises(ValueError):
        subtract_areas(10, holes)


def test_snap_rejects_negative_or_non_finite_tolerance():
    for tolerance in (-1, math.nan, math.inf):
        with pytest.raises(ValueError):
            snap_point(Point(0, 0), [Point(1, 1)], tolerance)


def test_invalid_measurement_does_not_mutate_store_or_consume_id():
    store = MeasurementStore()
    scale = ScaleCalibration.parse(100)
    with pytest.raises(ValueError):
        store.add_length([Point(0, 0), Point(math.nan, 0)], scale)
    assert store.all() == []
    valid = store.add_length([Point(0, 0), Point(1, 0)], scale)
    assert valid.id == "M00001"
