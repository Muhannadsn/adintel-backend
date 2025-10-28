#!/usr/bin/env python3
"""
Unit tests for the LLaVA text sanitization helper in VisionExtractor.
"""

import unittest

from agents.vision_extractor import VisionExtractor


class VisionExtractorSanitizerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.extractor = VisionExtractor()

    def test_visible_text_section_isolated(self):
        llava_output = (
            "1. ALL visible text:\n"
            "Rafeeq\n"
            "Download the Rafeeq app\n"
            "Free delivery on your first order\n"
            "\n"
            "2. Product or service being advertised:\n"
            "Food delivery application\n"
            "\n"
            "5. Visual elements (colors, imagery, style):\n"
            "Orange background with a phone showing the Rafeeq app interface"
        )

        visible, visual, sections = self.extractor._extract_visible_text(llava_output)

        expected_visible = (
            "Rafeeq\nDownload the Rafeeq app\nFree delivery on your first order"
        )

        self.assertEqual(visible, expected_visible)
        self.assertEqual(
            visual,
            "Orange background with a phone showing the Rafeeq app interface",
        )
        self.assertIsNone(sections.get("brand"))
        self.assertIn("visible_text", sections)

    def test_meta_preface_removed_when_sections_missing(self):
        llava_output = (
            "1. The visible text in the image is:\n"
            "Talabat Pro\n"
            "Get 10% off your first three orders\n"
            "Join now!\n"
            "\n"
            "More details: the ad promotes a subscription.\n"
        )

        visible, visual, sections = self.extractor._extract_visible_text(llava_output)

        expected_visible = (
            "Talabat Pro\nGet 10% off your first three orders\nJoin now!"
        )

        self.assertEqual(visible, expected_visible)
        self.assertEqual(visual, "")
        self.assertIn("visible_text", sections)

    def test_plain_text_passes_through(self):
        raw_text = "Burger King\nDouble Whopper Meal\nOnly 25 QAR"
        visible, visual, sections = self.extractor._extract_visible_text(raw_text)

        self.assertEqual(visible, raw_text)
        self.assertEqual(visual, "")
        self.assertNotIn("visible_text", sections)


if __name__ == "__main__":
    unittest.main()
