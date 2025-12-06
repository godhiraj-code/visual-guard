from setuptools import setup, find_packages
import os

setup(
    name="visual-guard",
    version="0.2.1",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "selenium>=4.0.0",
        "Pillow>=9.0.0",
        "colorama>=0.4.0",
        "jinja2>=3.0.0",
        "scikit-image>=0.19.0",
        "numpy>=1.21.0",
        "imagehash>=4.3.0"
    ],
    author="dhiraj",
    author_email="dhirajdas.666@gmail.com",
    description="A robust visual regression testing library for Python.",
    long_description=open("README.md").read() if os.path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    url="https://github.com/godhiraj-code/visual-guard",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
