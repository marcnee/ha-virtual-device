"""Render assets/icon.svg into the PNGs Home Assistant shows for the integration.

Needs Playwright with Chromium (`pip install playwright && playwright install chromium`).
Run from the repository root: python scripts/render_brand.py
"""

from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).parents[1]
SVG = (ROOT / "assets/icon.svg").read_text()
BRAND = ROOT / "custom_components/virtual_device/brand"
SIZES = {"icon.png": 256, "icon@2x.png": 512}


def main() -> None:
    BRAND.mkdir(exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        for name, size in SIZES.items():
            page = browser.new_page(viewport={"width": size, "height": size})
            page.set_content(
                f"<style>html,body{{margin:0;background:transparent}}"
                f"svg{{display:block;width:{size}px;height:{size}px}}</style>{SVG}"
            )
            page.screenshot(path=str(BRAND / name), omit_background=True)
            page.close()
        browser.close()


if __name__ == "__main__":
    main()
