from selenium import webdriver
from selenium.webdriver.common.by import By
from visual_guard import VisualTester, SimpleReporter, setup_logger
import time
import os

# Setup
logger = setup_logger("visual_demo")
driver = webdriver.Chrome()
visual = VisualTester()
reporter = SimpleReporter("Visual Regression Demo")

try:
    # 1. Open a page
    driver.get("https://www.google.com")
    time.sleep(2) # Wait for load
    
    # 2. Full Page Check (First run creates baseline)
    logger.info("Running Test 1: Full Page")
    if visual.assert_matches(driver, "google_home"):
        reporter.add_result("Google Home - Full", "PASSED", 
                            baseline_path="tests/baselines/google_home.png",
                            snapshot_path="tests/snapshots/google_home.png")
    else:
        reporter.add_result("Google Home - Full", "FAILED",
                            baseline_path="tests/baselines/google_home.png",
                            snapshot_path="tests/snapshots/google_home.png",
                            diff_path="tests/snapshots/diffs/google_home_diff.png")

    # 3. Region Selection (Search Bar)
    logger.info("Running Test 2: Region Selection")
    # Google's search bar usually has name='q'
    search_bar = driver.find_element(By.NAME, "q")
    if visual.assert_matches(search_bar, "google_search_bar"):
        reporter.add_result("Google Search Bar", "PASSED",
                            baseline_path="tests/baselines/google_search_bar.png",
                            snapshot_path="tests/snapshots/google_search_bar.png")
    else:
        reporter.add_result("Google Search Bar", "FAILED",
                            baseline_path="tests/baselines/google_search_bar.png",
                            snapshot_path="tests/snapshots/google_search_bar.png",
                            diff_path="tests/snapshots/diffs/google_search_bar_diff.png")

    # 4. Masking (Simulate dynamic content)
    # Let's pretend the search bar is dynamic and mask it out.
    logger.info("Running Test 3: Masking")
    search_bar = driver.find_element(By.NAME, "q")
    rect = search_bar.rect
    # Region format: (x, y, w, h)
    mask_region = (int(rect['x']), int(rect['y']), int(rect['width']), int(rect['height']))
    
    # We will modify the page to force a change in the search bar, but mask it.
    # If masking works, the test should PASS despite the change.
    search_bar.send_keys("Ignore this text")
    
    # Note: We need to use the SAME baseline name to compare against the previous clean state?
    # No, let's create a new test case for masking.
    # First run: creates baseline (with text 'Ignore this text' masked? No, baseline is raw)
    # Actually, for masking to be useful, we usually compare against a baseline that MIGHT have different content in that area.
    # Let's use "google_masked".
    
    if visual.assert_matches(driver, "google_masked", exclude_regions=[mask_region]):
        reporter.add_result("Google Masked", "PASSED",
                            baseline_path="tests/baselines/google_masked.png",
                            snapshot_path="tests/snapshots/google_masked.png")
    else:
        reporter.add_result("Google Masked", "FAILED",
                            baseline_path="tests/baselines/google_masked.png",
                            snapshot_path="tests/snapshots/google_masked.png",
                            diff_path="tests/snapshots/diffs/google_masked_diff.png")

finally:
    driver.quit()
    reporter.generate("visual_report.html")
