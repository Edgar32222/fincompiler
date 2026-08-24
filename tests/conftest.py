from pathlib import Path

import pytest


@pytest.fixture
def demo_dir():
    return Path(__file__).parents[1] / "demo" / "nova_appliances"

