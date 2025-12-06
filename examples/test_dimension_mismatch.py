import sys
import os
from PIL import Image

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from visual_guard import VisualTester
from visual_guard.exceptions import ComparisonError

def test_dimension_mismatch():
    tester = VisualTester(snapshot_dir="tests_v021")
    
    # Create a dummy baseline (100x100)
    baseline_img = Image.new("RGB", (100, 100), color="white")
    baseline_path = os.path.join(tester.baseline_dir, "size_test.png")
    baseline_img.save(baseline_path)
    print(f"Created baseline: {baseline_path} (100x100)")

    # Create a dummy current image (100x101) - Mismatch!
    current_img = Image.new("RGB", (100, 101), color="white")
    
    print("Running comparison with mismatched dimensions...")
    try:
        tester.assert_matches(current_img, "size_test")
        print("FAIL: Expected assertion to raise ComparisonError, but it passed!")
    except ComparisonError as e:
        print(f"PASS: Caught expected error: {e}")
    except Exception as e:
        print(f"FAIL: Caught unexpected exception: {type(e).__name__}: {e}")

if __name__ == "__main__":
    test_dimension_mismatch()
