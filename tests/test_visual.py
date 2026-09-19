import math

import numpy as np
import pytest
from PIL import Image

import visual_guard.visual as visual_module
from visual_guard import VisualTester
from visual_guard.exceptions import ComparisonError


def _tester(tmp_path):
    return VisualTester(
        baseline_dir=str(tmp_path / "baselines"),
        snapshot_dir=str(tmp_path / "snapshots"),
    )


@pytest.mark.parametrize(
    ("method", "threshold"),
    [
        ("pixel", -0.1),
        ("pixel", 100.1),
        ("ssim", math.inf),
        ("phash", 65),
        ("unknown", 0),
    ],
)
def test_rejects_invalid_method_thresholds_before_creating_baseline(tmp_path, method, threshold):
    tester = _tester(tmp_path)

    with pytest.raises(ComparisonError):
        tester.assert_matches(Image.new("RGB", (8, 8), "white"), "invalid", method=method, threshold=threshold)

    assert not (tmp_path / "baselines" / "invalid.png").exists()


@pytest.mark.parametrize(
    ("score", "threshold", "expected"),
    [
        (1.0, 0.0, True),
        (0.95, 5.0, True),
        (0.949, 5.0, False),
    ],
)
def test_ssim_threshold_is_maximum_difference_percentage(monkeypatch, tmp_path, score, threshold, expected):
    monkeypatch.setattr(
        visual_module,
        "ssim",
        lambda first, second, full: (score, np.ones_like(first, dtype=float)),
    )
    tester = _tester(tmp_path)
    image = Image.new("RGB", (8, 8), "white")

    assert tester.assert_matches(image, "sample", method="ssim", threshold=threshold)
    assert tester.assert_matches(image, "sample", method="ssim", threshold=threshold) is expected
