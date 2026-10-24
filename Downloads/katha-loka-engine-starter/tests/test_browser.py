import unittest
from pathlib import Path
from playwright.sync_api import sync_playwright


BASE_URL = "http://127.0.0.1:8788"


class KathaLokaBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)
        cls.page = cls.browser.new_page(
            viewport={"width": 1280, "height": 900}
        )
        cls.errors = []
        cls.page.on("pageerror", lambda error: cls.errors.append(str(error)))

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def test_homepage_loads(self):
        response = self.page.goto(BASE_URL, wait_until="networkidle")
        self.assertIsNotNone(response)
        self.assertEqual(response.status, 200)
        self.assertTrue(self.page.locator("body").inner_text().strip())

    def test_homepage_has_story_content(self):
        self.page.goto(BASE_URL, wait_until="networkidle")
        content = self.page.locator("body").inner_text().lower()
        self.assertTrue(
            "katha" in content or "story" in content or "tortoise" in content,
            "Expected story-related content on the homepage",
        )

    def test_cover_images_load(self):
        self.page.goto(BASE_URL, wait_until="networkidle")
        images = self.page.locator("img")
        for i in range(images.count()):
            image = images.nth(i)
            if image.is_visible():
                self.assertTrue(
                    image.evaluate(
                        "(img) => img.complete && img.naturalWidth > 0"
                    ),
                    f"Image failed to load: {image.get_attribute('src')}",
                )

    def test_mobile_layout_has_no_horizontal_overflow(self):
        self.page.set_viewport_size({"width": 390, "height": 844})
        self.page.goto(BASE_URL, wait_until="networkidle")
        dimensions = self.page.evaluate(
            """() => ({
                viewport: document.documentElement.clientWidth,
                page: document.documentElement.scrollWidth
            })"""
        )
        self.assertLessEqual(
            dimensions["page"],
            dimensions["viewport"],
            f"Horizontal overflow on mobile: {dimensions}",
        )

    def test_no_javascript_exceptions(self):
        self.page.goto(BASE_URL, wait_until="networkidle")
        self.assertEqual(self.errors, [], "\n".join(self.errors))


if __name__ == "__main__":
    unittest.main(verbosity=2)
