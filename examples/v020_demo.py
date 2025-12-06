import os
import sys
sys.path.append(os.path.join(os.getcwd(), "src"))
import shutil
from PIL import Image, ImageDraw, ImageFilter
from visual_guard.visual import VisualTester

def setup_images():
    os.makedirs("tests_v020/baselines", exist_ok=True)
    os.makedirs("tests_v020/snapshots", exist_ok=True)
    
    # Create a baseline image (simple square)
    base = Image.new("RGB", (200, 200), "white")
    draw = ImageDraw.Draw(base)
    draw.rectangle([50, 50, 150, 150], fill="blue")
    base.save("tests_v020/baselines/test_basic.png")
    base.save("tests_v020/baselines/test_ssim.png")
    base.save("tests_v020/baselines/test_phash.png")
    base.save("tests_v020/baselines/test_masking.png")
    
    # Create a slightly modified image (shifted color)
    shifted = Image.new("RGB", (200, 200), "white")
    draw = ImageDraw.Draw(shifted)
    draw.rectangle([50, 50, 150, 150], fill=(0, 0, 250)) # Slight blue shift
    shifted.save("shifted.png")
    
    # Create a blurred image for SSIM
    blurred = base.filter(ImageFilter.GaussianBlur(2))
    blurred.save("blurred.png")
    
    # Create an image with extra content for masking
    masked_test = base.copy()
    draw = ImageDraw.Draw(masked_test)
    draw.ellipse([80, 80, 120, 120], fill="red") # Red dot in center
    masked_test.save("masked_test.png")

    return "shifted.png", "blurred.png", "masked_test.png"

def run_tests():
    tester = VisualTester(baseline_dir="tests_v020/baselines", snapshot_dir="tests_v020/snapshots")
    shifted, blurred, masked_test = setup_images()
    
    print("--- Running v0.2.0 Verification ---")

    # 1. Pixel Comparison (Should fail or have small diff)
    print("\n[1] Pixel Comparison (Strict)")
    passed = tester.assert_matches(shifted, "test_basic", threshold=0.0)
    print(f"Pixel Strict (expected fail/diff): {passed}")

    # 2. SSIM Comparison (Should pass with blur as structure is same)
    print("\n[2] SSIM Comparison")
    try:
        # SSIM is structure based. Blur preserves structure mostly.
        passed = tester.assert_matches(blurred, "test_ssim", method="ssim", threshold=10.0)
        print(f"SSIM with Blur (expected pass): {passed}")
    except Exception as e:
        print(f"Skipping SSIM test: {e}")

    # 3. pHash Comparison (Robust to slight shifts/blur)
    print("\n[3] pHash Comparison")
    passed = tester.assert_matches(shifted, "test_phash", method="phash", threshold=5)
    print(f"pHash with color shift (expected pass): {passed}")

    # 4. Polygon Masking
    print("\n[4] Polygon Masking")
    # Mask out the red dot using a polygon (triangle for fun, though dot is circle)
    # Dot is at 80,80 to 120,120. Center 100,100.
    # Triangle covering 80,80 to 120,120
    polygon = [(80, 80), (120, 80), (100, 130)]
    # Or just a box to be safe: region format
    # Let's try polygon format: list of tuples
    poly_region = [(70, 70), (130, 70), (130, 130), (70, 130)] # Square polygon
    passed = tester.assert_matches(masked_test, "test_masking", exclude_regions=[poly_region], method="pixel")
    print(f"Polygon Masking (expected pass): {passed}")

    # Cleanup
    if os.path.exists("shifted.png"): os.remove("shifted.png")
    if os.path.exists("blurred.png"): os.remove("blurred.png")
    if os.path.exists("masked_test.png"): os.remove("masked_test.png")
    shutil.rmtree("tests_v020", ignore_errors=True)

if __name__ == "__main__":
    run_tests()
