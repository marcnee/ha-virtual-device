"""Home Assistant shows the images in brand/ for the integration (no CDN entry needed)."""

import struct
from pathlib import Path

import pytest

BRAND = Path(__file__).parents[1] / "custom_components/virtual_device/brand"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
RGBA = 6  # PNG colour type with an alpha channel: the icon has transparent corners

# Names Home Assistant serves (homeassistant/components/brands/const.py).
ALLOWED = {
    "icon.png",
    "logo.png",
    "icon@2x.png",
    "logo@2x.png",
    "dark_icon.png",
    "dark_logo.png",
    "dark_icon@2x.png",
    "dark_logo@2x.png",
}


def png_info(path: Path) -> tuple[int, int, int]:
    """Width, height and colour type from the PNG header."""
    data = path.read_bytes()
    assert data.startswith(PNG_SIGNATURE), f"{path.name} is not a PNG"
    width, height, _depth, colour_type = struct.unpack(">IIBB", data[16:26])
    return width, height, colour_type


@pytest.mark.parametrize(("name", "size"), [("icon.png", 256), ("icon@2x.png", 512)])
def test_icon_is_a_square_png_with_transparency(name: str, size: int) -> None:
    assert png_info(BRAND / name) == (size, size, RGBA)


def test_only_images_that_home_assistant_serves_are_shipped() -> None:
    assert {p.name for p in BRAND.iterdir()} <= ALLOWED
