# Visual Guard

[![Visual Guard CI](https://github.com/godhiraj-code/visual-guard/actions/workflows/ci.yml/badge.svg)](https://github.com/godhiraj-code/visual-guard/actions/workflows/ci.yml)

**Visual Guard** is a powerful Python library designed specifically for **Visual Regression Testing**. It allows you to automatically detect UI changes by comparing screenshots against approved baselines, ensuring your application looks perfect on every release.

## Key Features

- **Multiple Comparison Methods**:
    - **Pixel**: Strict pixel-perfect matching.
    - **SSIM** (Structural Similarity): Human-eye perception matching (requires `scikit-image`).
    - **pHash** (Perceptual Hash): Robust matching that ignores minor color shifts or scaling.
- **Advanced Region Masking**: Easily exclude dynamic content (like timestamps, ads, or carousels) using **Rectangles** or **Polygons**.
- **Visual Reporting**: Generates professional HTML reports with side-by-side views of Baseline, Actual, and Diff images.
- **Cross-Platform**: Works seamlessly with **Selenium WebDriver** (Web) and **Appium** (Mobile).
- **CI/CD Ready**: Integrated with GitHub Actions for automated verification.

## Installation

### Basic Installation
```bash
pip install visual-guard
```

### Full Installation (Recommended)
To enable **SSIM** comparison, install the extra dependencies:
```bash
pip install visual-guard[full]
# OR manually
pip install scikit-image numpy imagehash
```

*Note: On some platforms (e.g., bleeding-edge Python versions), `scikit-image` may not have pre-built wheels. Visual Guard will gracefully fall back to Pixel/pHash methods if SSIM is unavailable.*

## Quick Start

### Web Automation

```python
from visual_guard import VisualTester
from selenium import webdriver

# 1. Setup Driver
driver = webdriver.Chrome()
driver.get("https://example.com")

# 2. Initialize Visual Guard
visual = VisualTester()

# 3. Compare Full Page (Default: Pixel)
# First run creates the baseline. Subsequent runs compare against it.
visual.assert_matches(driver, "homepage")

# 4. Compare using SSIM (Structural Similarity)
# Useful for handling minor rendering differences across browsers
visual.assert_matches(driver, "homepage_ssim", method="ssim", threshold=0.95)

# 5. Compare using pHash (Perceptual Hash)
# Best for ignoring minor color shifts or anti-aliasing noise
visual.assert_matches(driver, "homepage_phash", method="phash", threshold=5)
```

### Advanced Masking

Ignore dynamic areas to keep tests stable. You can now use Polygons!

```python
# Mask a simple rectangle (x, y, width, height)
# Useful for banners or fixed headers
visual.assert_matches(driver, "dashboard", exclude_regions=[(100, 50, 200, 30)])

# Mask a complex Polygon shape (list of x,y points)
# Useful for irregular shapes, logos, or floating action buttons
visual.assert_matches(driver, "map_view", exclude_regions=[
    [(10, 10), (50, 10), (50, 50), (10, 50)] # A custom quad
])
```

### Reporting

Generate a comprehensive visual report to see exactly what changed:

```python
from visual_guard import SimpleReporter

reporter = SimpleReporter()

try:
    visual.assert_matches(driver, "homepage")
    reporter.add_result("homepage", True, "tests/baselines/homepage.png", "tests/snapshots/homepage.png")
except Exception as e:
    reporter.add_result("homepage", False, "tests/baselines/homepage.png", "tests/snapshots/homepage.png", "tests/diffs/homepage_diff.png")

reporter.generate("visual_report.html")
```

## Comparison Methods Guide

| Method | Best For | Threshold | Note |
|--------|----------|-----------|------|
| **pixel** | Icons, Logos, Strict UI elements | 0.0 - 100.0 (Percent diff) | Default. Very sensitive. |
| **ssim** | Complex layouts, Text blocks | 0.0 - 1.0 (Similarity score) | Requires `scikit-image`. Best for general UI. |
| **phash** | Dynamic content, Cross-browser | 0 - 64 (Hamming distance) | Extremely robust to minor pixel shifts. |
