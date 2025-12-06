import os
import time
import functools
import numpy as np
from PIL import Image, ImageChops, ImageDraw
from io import BytesIO
try:
    from skimage.metrics import structural_similarity as ssim
except ImportError:
    ssim = None
import imagehash
from .logger import setup_logger
from .exceptions import VisualGuardError, ImageLoadError, ComparisonError, BaselineMissingError

logger = setup_logger("visual_guard.visual")

@functools.lru_cache(maxsize=32)
def _load_image_file(path):
    """Cached image loader."""
    return Image.open(path).convert("RGB")

class VisualTester:
    """
    Handles visual regression testing by comparing screenshots against baselines.
    Compatible with Selenium WebDriver (Web) and Appium (Mobile).
    """

    def __init__(self, baseline_dir="tests/baselines", snapshot_dir="tests/snapshots"):
        self.baseline_dir = baseline_dir
        self.snapshot_dir = snapshot_dir
        self.diff_dir = os.path.join(snapshot_dir, "diffs")
        
        os.makedirs(self.baseline_dir, exist_ok=True)
        os.makedirs(self.snapshot_dir, exist_ok=True)
        os.makedirs(self.diff_dir, exist_ok=True)

    def _process_image(self, image_data):
        """Converts input (path, bytes, WebElement) to PIL Image."""
        try:
            if isinstance(image_data, str):
                if os.path.exists(image_data):
                    # Use cached loader if it's a file path
                    return _load_image_file(image_data)
                else:
                    raise FileNotFoundError(f"Image not found: {image_data}")
            elif isinstance(image_data, bytes):
                return Image.open(BytesIO(image_data)).convert("RGB")
            elif hasattr(image_data, "screenshot_as_png"): # Selenium WebElement
                png_data = image_data.screenshot_as_png
                return Image.open(BytesIO(png_data)).convert("RGB")
            elif hasattr(image_data, "get_screenshot_as_png"): # Selenium WebDriver
                png_data = image_data.get_screenshot_as_png()
                return Image.open(BytesIO(png_data)).convert("RGB")
            elif isinstance(image_data, Image.Image): # PIL Image object
                return image_data.convert("RGB")
            else:
                # Try to see if it's a base64 string directly
                try:
                    import base64
                    return Image.open(BytesIO(base64.b64decode(image_data))).convert("RGB")
                except:
                    pass
                raise ValueError(f"Unsupported image format: {type(image_data)}")
        except Exception as e:
            raise ImageLoadError(f"Failed to process image: {e}") from e

    def _mask_regions(self, image, regions):
        """Draws black rectangles or polygons over excluded regions."""
        if not regions:
            return image
        
        masked_image = image.copy()
        draw = ImageDraw.Draw(masked_image)
        
        for region in regions:
            # Region format: (x, y, width, height) or [(x1, y1), (x2, y2), ...]
            if isinstance(region, (list, tuple)):
                if len(region) == 4 and all(isinstance(n, (int, float)) for n in region):
                    x, y, w, h = region
                    draw.rectangle([x, y, x + w, y + h], fill="black")
                elif len(region) >= 3 and all(isinstance(p, (list, tuple)) and len(p) == 2 for p in region):
                    # Polygon: List of (x, y) points
                    # draw.polygon expects flat list or list of tuples
                    draw.polygon(region, fill="black")
                else:
                    logger.warning(f"Invalid region format: {region}. Expected (x, y, w, h) or list of points.")
            else:
                logger.warning(f"Invalid region type: {type(region)}")
                
        return masked_image

    def crop_region(self, image_data, region):
        """Crops a specific region from the image."""
        image = self._process_image(image_data)
        x, y, w, h = region
        return image.crop((x, y, x + w, y + h))

    def assert_matches(self, image_data, name, threshold=0.1, exclude_regions=None):
        """
        Compares the provided image against the baseline.
        
        Args:
            image_data: The current screenshot (path, bytes, or WebElement).
            name: Unique name for the test case.
            threshold: Allowed pixel difference percentage (0.0 to 100.0).
            exclude_regions: List of (x, y, w, h) tuples to ignore.
            
        Returns:
            bool: True if matches (or new baseline created), False otherwise.
        """
        current_image = self._process_image(image_data)
        
        # Apply masking if needed
        if exclude_regions:
            current_image = self._mask_regions(current_image, exclude_regions)

        baseline_path = os.path.join(self.baseline_dir, f"{name}.png")
        snapshot_path = os.path.join(self.snapshot_dir, f"{name}.png")
        diff_path = os.path.join(self.diff_dir, f"{name}_diff.png")

        # Save current snapshot
        current_image.save(snapshot_path)

        # 1. First Run: Create Baseline
        if not os.path.exists(baseline_path):
            current_image.save(baseline_path)
            logger.info(f"Baseline created for '{name}' at {baseline_path}")
            return True

        # 2. Compare
        baseline_image = Image.open(baseline_path).convert("RGB")
        
        # Ensure dimensions match
        if current_image.size != baseline_image.size:
            logger.error(f"Image dimensions mismatch for '{name}': {current_image.size} vs {baseline_image.size}")
            # Resize baseline to match current (simple approach, or fail)
            # For strict testing, we should probably fail or resize current to baseline.
            # Let's resize current to match baseline for comparison sake if close? 
            # No, strict fail is better for visual regression.
            # But to generate a diff, we need same size.
            current_image = current_image.resize(baseline_image.size)

        # Calculate difference
    def _compare_pixels(self, img1, img2, threshold):
        """Pixel-by-pixel comparison."""
        diff = ImageChops.difference(img1, img2)
        if diff.getbbox():
            diff_gray = diff.convert("L")
            histogram = diff_gray.histogram()
            total_pixels = img1.width * img1.height
            matching_pixels = histogram[0]
            diff_pixels = total_pixels - matching_pixels
            diff_percent = (diff_pixels / total_pixels) * 100
            return diff_percent <= threshold, diff_percent, diff
        return True, 0.0, diff

    def _compare_ssim(self, img1, img2, threshold):
        """Structural Similarity Index (SSIM) comparison."""
        if ssim is None:
            raise VisualGuardError("scikit-image is required for SSIM comparison. Install it with 'pip install scikit-image'.")
        
        # Convert to grayscale for SSIM
        img1_gray = np.array(img1.convert("L"))
        img2_gray = np.array(img2.convert("L"))
        
        score, diff_map = ssim(img1_gray, img2_gray, full=True)
        # SSIM score is -1 to 1. 1 means identical.
        # We want difference to match our threshold logic (0 is perfect, 100 is bad).
        # Typically SSIM >= 0.95 is good.
        # Let's map score to diff percent: (1 - score) * 100
        diff_percent = (1 - score) * 100
        
        # Create diff image from diff_map
        diff_image = Image.fromarray((diff_map * 255).astype(np.uint8))
        
        return diff_percent <= threshold, diff_percent, diff_image

    def _compare_phash(self, img1, img2, threshold):
        """Perceptual Hash comparison."""
        hash1 = imagehash.phash(img1)
        hash2 = imagehash.phash(img2)
        
        # Hamming distance between hashes
        diff_score = hash1 - hash2
        
        # Normalize? Hamming distance 0 is match.
        # Threshold for phash is usually integer (0-5 is very close).
        # We'll treat 'threshold' as max allowed hamming distance if method is phash.
        return diff_score <= threshold, float(diff_score), None

    def assert_matches(self, image_data, name, threshold=0.1, exclude_regions=None, method="pixel"):
        """
        Compares the provided image against the baseline.
        
        Args:
            image_data: The current screenshot (path, bytes, or WebElement).
            name: Unique name for the test case.
            threshold: Allowed difference (Percent for pixel/ssim, Hamming distance for phash).
            exclude_regions: List of (x, y, w, h) rectangles or [(x,y),...] polygons.
            method: 'pixel', 'ssim', or 'phash'.
            
        Returns:
            bool: True if match.
        """
        try:
            current_image = self._process_image(image_data)
            
            # Apply masking
            if exclude_regions:
                current_image = self._mask_regions(current_image, exclude_regions)

            baseline_path = os.path.join(self.baseline_dir, f"{name}.png")
            snapshot_path = os.path.join(self.snapshot_dir, f"{name}.png")
            diff_path = os.path.join(self.diff_dir, f"{name}_diff.png")

            current_image.save(snapshot_path)

            if not os.path.exists(baseline_path):
                current_image.save(baseline_path)
                logger.info(f"Baseline created for '{name}' at {baseline_path}")
                return True

            # Use cached loader for baseline if possible, then copy for masking
            # But here we just load
            baseline_image = _load_image_file(baseline_path).copy() # Copy to avoid mutating cached
            
            # Apply masking to baseline as well so we compare black-to-black (ignored)
            if exclude_regions:
                baseline_image = self._mask_regions(baseline_image, exclude_regions)
            
            # Resize if needed (strict check usually, but for ssim we need same size)
            if current_image.size != baseline_image.size:
                msg = f"Image dimensions mismatch for '{name}': {current_image.size} vs {baseline_image.size}"
                logger.error(msg)
                raise ComparisonError(msg)

            passed = False
            diff_val = 0.0
            diff_img = None

            if method == "pixel":
                passed, diff_val, diff_img = self._compare_pixels(current_image, baseline_image, threshold)
            elif method == "ssim":
                passed, diff_val, diff_img = self._compare_ssim(current_image, baseline_image, threshold)
            elif method == "phash":
                passed, diff_val, diff_img = self._compare_phash(current_image, baseline_image, threshold)
            else:
                raise ValueError(f"Unknown comparison method: {method}")

            if not passed:
                logger.error(f"Visual check failed ({method}) for '{name}'. Val: {diff_val:.2f} > {threshold}")
                if diff_img:
                    diff_img.save(diff_path)
                return False
            else:
                logger.info(f"Visual check passed ({method}) for '{name}'. Val: {diff_val:.2f}")
                return True
                
        except Exception as e:
            if isinstance(e, VisualGuardError):
                raise
            raise ComparisonError(f"Comparison failed for '{name}': {e}") from e
