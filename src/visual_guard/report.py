import os
import base64
from jinja2 import Template
from .logger import setup_logger

logger = setup_logger("visual_guard.report")

class SimpleReporter:
    """Generates a visual HTML report."""

    def __init__(self, title="Visual Regression Report"):
        self.title = title
        self.results = []

    def _image_to_base64(self, path):
        """Converts an image file to base64 string."""
        if not path or not os.path.exists(path):
            return ""
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def add_result(self, name, status, baseline_path=None, snapshot_path=None, diff_path=None, error=None):
        """Adds a visual test result to the report."""
        self.results.append({
            "name": name,
            "status": status,
            "baseline": self._image_to_base64(baseline_path),
            "snapshot": self._image_to_base64(snapshot_path),
            "diff": self._image_to_base64(diff_path),
            "error": str(error) if error else ""
        })

    def generate(self, output_path="report.html"):
        """Generates the HTML report file."""
        template_str = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>{{ title }}</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background-color: #f9f9f9; }
                h1 { color: #333; text-align: center; }
                .test-case { background: white; padding: 20px; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #eee; padding-bottom: 10px; margin-bottom: 15px; }
                .status { font-weight: bold; padding: 5px 10px; border-radius: 4px; }
                .passed { background-color: #d4edda; color: #155724; }
                .failed { background-color: #f8d7da; color: #721c24; }
                .images { display: flex; gap: 20px; justify-content: center; }
                .image-container { text-align: center; }
                img { max-width: 300px; border: 1px solid #ddd; border-radius: 4px; margin-top: 5px; cursor: pointer; transition: transform 0.2s; }
                img:hover { transform: scale(1.5); border-color: #333; z-index: 10; }
                .error { color: red; margin-top: 10px; }
            </style>
        </head>
        <body>
            <h1>{{ title }}</h1>
            {% for result in results %}
            <div class="test-case">
                <div class="header">
                    <h2>{{ result.name }}</h2>
                    <span class="status {{ result.status.lower() }}">{{ result.status }}</span>
                </div>
                
                {% if result.error %}
                <div class="error">Error: {{ result.error }}</div>
                {% endif %}

                <div class="images">
                    {% if result.baseline %}
                    <div class="image-container">
                        <strong>Baseline</strong><br>
                        <img src="data:image/png;base64,{{ result.baseline }}" alt="Baseline">
                    </div>
                    {% endif %}
                    
                    {% if result.snapshot %}
                    <div class="image-container">
                        <strong>Actual</strong><br>
                        <img src="data:image/png;base64,{{ result.snapshot }}" alt="Actual">
                    </div>
                    {% endif %}
                    
                    {% if result.diff %}
                    <div class="image-container">
                        <strong>Diff</strong><br>
                        <img src="data:image/png;base64,{{ result.diff }}" alt="Diff">
                    </div>
                    {% endif %}
                </div>
            </div>
            {% endfor %}
        </body>
        </html>
        """
        
        template = Template(template_str)
        html_content = template.render(title=self.title, results=self.results)
        
        with open(output_path, "w") as f:
            f.write(html_content)
        
        logger.info(f"Report generated at {os.path.abspath(output_path)}")
