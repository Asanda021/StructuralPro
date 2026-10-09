from core.drawings.graphical_takeoff import Point
from core.drawings.takeoff_session import DrawingTakeoffSession


def test_page_specific_calibrations_survive_session_serialization():
    session = DrawingTakeoffSession("multi-page-plan.pdf")
    session.calibrate(page=1, reference_pixels=100, reference_meters=10)
    session.calibrate(page=2, reference_pixels=200, reference_meters=5)
    session.set_page(2)
    item = session.add_length([Point(0, 0), Point(200, 0)], page=2)
    assert item.quantity == 5

    restored = DrawingTakeoffSession.from_dict(session.to_dict())
    assert restored.current_page == 2
    assert restored.calibrations[1].meters_per_pixel == 0.1
    assert restored.calibrations[2].meters_per_pixel == 0.025
    assert restored.calibration.page == 2
    assert restored.validate()["valid"] is True
    restored.set_page(1)
    assert restored.calibration.page == 1


def test_from_dict_rejects_invalid_persisted_calibration():
    import pytest

    data = {
        "drawing_source": "plan.pdf",
        "current_page": 1,
        "calibrations": {
            "1": {
                "meters_per_pixel": 0,
                "page": 1,
                "reference_pixels": 100,
                "reference_meters": 10,
                "source": "manual-reference",
            }
        },
        "items": [],
        "markups": [],
    }
    with pytest.raises(ValueError, match="کالیبراسیون نامعتبر"):
        DrawingTakeoffSession.from_dict(data)
