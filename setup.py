import re
from pathlib import Path

from setuptools import find_packages, setup

HERE = Path(__file__).parent


def read_version():
    text = (HERE / "marketcl" / "__init__.py").read_text()
    return re.search(r'__version__\s*=\s*"([^"]+)"', text).group(1)


setup(
    name="marketcl",
    version=read_version(),
    description="A command line paper trading game for the stock market, powered by Yahoo Finance.",
    long_description=(HERE / "README.md").read_text(),
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=["tests", "tests.*"]),
    python_requires=">=3.9",
    install_requires=[
        "click>=8.0",
        "rich>=13.0",
        "yfinance>=0.2.40",
    ],
    extras_require={
        "dev": ["pytest>=7.0"],
    },
    entry_points={
        "console_scripts": [
            "marketcl=marketcl.cli:cli",
            "mcl=marketcl.cli:cli",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Environment :: Console",
        "Topic :: Office/Business :: Financial",
    ],
)
