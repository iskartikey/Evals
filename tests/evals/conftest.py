"""Pytest configuration for the eval suite.

Loads the golden dataset from ``datasets/golden.json`` and exposes it as a
session-scoped fixture.
"""

import json
import os
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATASET_PATH = PROJECT_ROOT / "datasets" / "golden.json"


@pytest.fixture(scope="session")
def goldens() -> list[dict]:
    """Load the golden dataset from ``datasets/golden.json``."""
    with open(DATASET_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data["goldens"]
