from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).parents[1]))

from generate_ai import image_endpoint, load_dotenv


def test_image_endpoint_accepts_smai_service_root():
    assert image_endpoint("https://api.smai.ai") == "https://api.smai.ai/v1/images/generations"


def test_image_endpoint_preserves_full_generation_endpoint():
    endpoint = "https://api.smai.ai/v1/images/generations"
    assert image_endpoint(endpoint) == endpoint


def test_dotenv_loader_reads_values_without_exposing_secrets():
    values = load_dotenv(Path(__file__).with_name("fixture.env"))
    assert values == {"IMAGE_API_URL": "https://example.invalid", "IMAGE_API_KEY": "secret"}
