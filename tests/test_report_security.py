from PIL import Image

from visual_guard.report import SimpleReporter
from visual_guard.visual import _load_image_file


def test_report_escapes_page_controlled_values(tmp_path):
    payload = '<img src=x onerror="alert(1)">'
    reporter = SimpleReporter(payload)
    reporter.add_result(payload, 'failed" onclick="alert(1)', error=payload)
    output = tmp_path / "report.html"
    reporter.generate(output)
    html = output.read_text(encoding="utf-8")
    assert payload not in html
    assert '&lt;img src=x onerror=' in html
    assert 'class="status failed" onclick=' not in html


def test_replaced_image_is_reloaded_and_cached_image_is_not_mutable(tmp_path):
    path = tmp_path / "baseline.png"
    Image.new("RGB", (8, 8), "white").save(path)
    first = _load_image_file(str(path))
    first.putpixel((0, 0), (0, 0, 0))
    assert _load_image_file(str(path)).getpixel((0, 0)) == (255, 255, 255)
    Image.new("RGB", (9, 9), "black").save(path)
    replaced = _load_image_file(str(path))
    assert replaced.size == (9, 9)
    assert replaced.getpixel((0, 0)) == (0, 0, 0)
