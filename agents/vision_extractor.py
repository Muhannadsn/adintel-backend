#!/usr/bin/env python3
"""
Agent 0: Vision Extraction Layer - PaddleOCR + LLaVA

Uses PaddleOCR for accurate text extraction and LLaVA for visual understanding.
PaddleOCR provides superior OCR accuracy compared to LLaVA alone.
"""

from __future__ import annotations

import requests
import json
import base64
import re
from typing import Optional, Dict, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from paddleocr import PaddleOCR


@dataclass
class VisionExtractionResult:
    """Combined results from vision models."""
    extracted_text: str  # Text found in ad
    visual_description: str  # What the ad looks like
    confidence: float  # Overall extraction confidence
    deepseek_text: str  # DeepSeek OCR output
    llava_analysis: str  # LLaVA visual analysis
    method_used: str  # "parallel" or "fallback"
    sections: Dict[str, str] = field(default_factory=dict)


class VisionExtractor:
    """
    Layer 0: Vision Extraction - THE FOUNDATION

    Without this layer, the orchestrator is blind!
    """

    def __init__(self, ollama_host: str = "http://localhost:11434"):
        self.ollama_host = ollama_host
        self.llava_model = "llava:latest"
        # Initialize PaddleOCR for accurate text extraction
        self.paddle_ocr = None  # Lazy load to avoid initialization delays

    def extract(self, image_url: str, local_path: Optional[str] = None) -> VisionExtractionResult:
        """
        Extract text and visual information from ad image.

        Uses PaddleOCR for accurate text extraction (primary method).

        Args:
            image_url: URL of the ad image
            local_path: Optional local file path (if already downloaded)

        Returns:
            VisionExtractionResult with combined analysis
        """
        print(f"   🔍 [Vision Layer] Analyzing image...")

        # Get image path (PaddleOCR works with file paths)
        if local_path:
            image_path = local_path
        else:
            # Download image if URL provided
            image_data = self._get_image_data(image_url, local_path)
            if not image_data:
                print(f"   ❌ Failed to load image")
                return self._create_fallback_result("Image load failed")
            # Save temporarily for PaddleOCR
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
                tmp.write(image_data)
                image_path = tmp.name

        # RUN PADDLEOCR (PRIMARY METHOD - ACCURATE OCR)
        paddle_text = self._extract_with_paddleocr(image_path)

        # If PaddleOCR succeeds, use it as the primary text source
        if paddle_text:
            # Create result from PaddleOCR
            merged = VisionExtractionResult(
                extracted_text=paddle_text,
                visual_description="",  # PaddleOCR doesn't provide visual context
                confidence=0.95,  # PaddleOCR is highly accurate
                deepseek_text="",
                llava_analysis=paddle_text,  # Store OCR text here too for compatibility
                method_used="paddleocr",
                sections={},
            )

            print(f"   ✅ PaddleOCR extracted {len(paddle_text)} chars")
            return merged

        # FALLBACK: If PaddleOCR fails, use LLaVA
        print(f"   ⚠️  PaddleOCR failed, falling back to LLaVA...")
        image_data = self._get_image_data(image_url, local_path)
        if not image_data:
            return self._create_fallback_result("Both PaddleOCR and image load failed")

        llava_raw = self._extract_with_llava(image_data)
        clean_text, visual_description, sections = self._extract_visible_text(llava_raw)
        full_text = clean_text if clean_text and len(clean_text) > 100 else llava_raw

        merged = VisionExtractionResult(
            extracted_text=full_text,
            visual_description=visual_description or llava_raw,
            confidence=0.70,  # Lower confidence for LLaVA fallback
            deepseek_text="",
            llava_analysis=llava_raw,
            method_used="llava_fallback",
            sections=sections,
        )

        print(f"   ✅ LLaVA fallback extracted {len(merged.extracted_text)} chars")
        return merged

    def _get_image_data(self, image_url: str, local_path: Optional[str] = None) -> Optional[bytes]:
        """Download or load image data."""
        try:
            if local_path and Path(local_path).exists():
                # Load from local file
                with open(local_path, 'rb') as f:
                    return f.read()
            else:
                # Download from URL
                response = requests.get(image_url, timeout=10)
                response.raise_for_status()
                return response.content
        except Exception as e:
            print(f"   ⚠️  Error loading image: {e}")
            return None

    def _extract_with_deepseek(self, image_data: bytes) -> str:
        """
        Agent 0A: MiniCPM-V Fast OCR

        Specialized for fast text extraction from images (3-5 sec vs 45-90 sec).
        """
        try:
            # Encode image to base64
            image_b64 = base64.b64encode(image_data).decode('utf-8')

            # DeepSeek prompt optimized for OCR
            prompt = """Extract ALL visible text from this image. Include:
- Main headlines/titles
- Product names
- Prices and offers
- Any promotional text
- Brand names
- Fine print

Return ONLY the extracted text, no analysis or commentary."""

            # Call Ollama API
            response = requests.post(
                f"{self.ollama_host}/api/generate",
                json={
                    "model": self.deepseek_model,
                    "prompt": prompt,
                    "images": [image_b64],
                    "stream": False
                },
                timeout=90
            )

            if response.status_code == 200:
                result = response.json()
                extracted = result.get("response", "").strip()
                print(f"   ✅ MiniCPM-V OCR: {len(extracted)} chars")
                return extracted
            else:
                print(f"   ⚠️  MiniCPM-V failed: HTTP {response.status_code}")
                return ""

        except Exception as e:
            print(f"   ⚠️  MiniCPM-V error: {e}")
            return ""

    def _extract_with_paddleocr(self, image_path: str) -> str:
        """
        Extract text using PaddleOCR (highly accurate OCR).

        Args:
            image_path: Path to image file

        Returns:
            Extracted text as a single string
        """
        try:
            # Lazy load PaddleOCR to avoid startup delays
            if self.paddle_ocr is None:
                # Enable both Arabic and English for GCC market ads
                self.paddle_ocr = PaddleOCR(lang='arabic', use_angle_cls=True, show_log=False)

            # Run OCR
            result = self.paddle_ocr.predict(image_path)

            if not result or len(result) == 0:
                print(f"   ⚠️  PaddleOCR returned no results")
                return ""

            # Extract text from result
            texts = result[0].get('rec_texts', [])
            if not texts:
                print(f"   ⚠️  PaddleOCR found no text")
                return ""

            # Join all text lines with spaces
            full_text = " ".join(texts)
            return full_text.strip()

        except Exception as e:
            print(f"   ⚠️  PaddleOCR error: {e}")
            return ""

    def _extract_with_llava(self, image_data: bytes) -> str:
        """
        Agent 0B: LLaVA Vision Analysis

        Provides visual context and understanding.
        """
        try:
            # Encode image to base64
            image_b64 = base64.b64encode(image_data).decode('utf-8')

            # LLaVA prompt - PURE OCR ONLY
            prompt = """Extract ALL visible text from this image exactly as written.

Read every word, number, and symbol you see. Do not analyze, interpret, or describe the image.
Just transcribe the text character by character.

Return ONLY the extracted text."""

            # Call Ollama API
            response = requests.post(
                f"{self.ollama_host}/api/generate",
                json={
                    "model": self.llava_model,
                    "prompt": prompt,
                    "images": [image_b64],
                    "stream": False
                },
                timeout=90
            )

            if response.status_code == 200:
                result = response.json()
                analysis = result.get("response", "").strip()
                print(f"   ✅ LLaVA analysis: {len(analysis)} chars")
                return analysis
            else:
                print(f"   ⚠️  LLaVA failed: HTTP {response.status_code}")
                return ""

        except Exception as e:
            print(f"   ⚠️  LLaVA error: {e}")
            return ""

    def _extract_visible_text(self, llava_output: str) -> Tuple[str, str, Dict[str, str]]:
        """
        Clean LLaVA output so downstream agents receive only ad copy.

        Returns:
            (visible_text, visual_description, sections)
        """
        if not llava_output:
            return "", "", {}

        raw_sections = self._parse_llava_sections(llava_output)
        sections = {
            key: self._remove_commentary_lines(value)
            for key, value in raw_sections.items()
            if value
        }
        visible_text = sections.get("visible_text", "").strip()

        if not visible_text:
            visible_text = self._strip_meta_preface(llava_output)
        if not visible_text:
            visible_text = llava_output.strip()

        # Prefer explicit visual elements from LLaVA, fallback to product/service insight
        visual_description = (
            sections.get("visual_elements")
            or sections.get("product_service")
            or ""
        ).strip()

        visible_clean = self._remove_commentary_lines(visible_text)
        visual_clean = self._remove_commentary_lines(visual_description)

        return visible_clean, visual_clean, sections

    def _parse_llava_sections(self, llava_output: str) -> Dict[str, str]:
        """
        Parse numbered sections returned by LLaVA into a structured dict.
        """
        section_alias = {
            1: "visible_text",
            2: "product_service",
            3: "brand",
            4: "offers",
            5: "visual_elements",
        }

        sections: Dict[str, str] = {}
        current_key: Optional[str] = None
        buffer: list[str] = []

        for raw_line in llava_output.splitlines():
            line = raw_line.strip()
            if not line:
                if buffer:
                    buffer.append("")
                continue

            match = re.match(r"^(\d+)\.\s*(.*)$", line)
            if match:
                # Flush previous section
                if current_key and buffer:
                    sections[current_key] = "\n".join(l for l in buffer).strip()

                number = int(match.group(1))
                current_key = section_alias.get(number, f"section_{number}")
                buffer = []

                _, initial_content = self._split_section_header(match.group(2))
                if initial_content:
                    buffer.append(initial_content)
                continue

            if current_key:
                buffer.append(line)

        if current_key and buffer:
            sections[current_key] = "\n".join(l for l in buffer).strip()

        return sections

    def _split_section_header(self, header_line: str) -> Tuple[str, str]:
        """
        Split a section header like "ALL visible text: ..." into (title, content).
        """
        cleaned = header_line.strip()
        if ":" in cleaned:
            title, content = cleaned.split(":", 1)
            return title.strip(), content.strip()
        return cleaned, ""

    def _strip_meta_preface(self, llava_output: str) -> str:
        """
        Remove LLaVA's instructional scaffolding and keep only ad copy.
        """
        lines = []
        collecting = False

        for raw_line in llava_output.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            numbered = re.match(r"^(\d+)\.\s*(.*)$", line)
            if numbered:
                number = numbered.group(1)
                content = numbered.group(2).strip().lower()

                if number != "1" and collecting:
                    break  # finished visible-text section

                if number == "1" and any(
                    phrase in content
                    for phrase in (
                        "visible text",
                        "text in the image",
                        "all text",
                        "extract",
                    )
                ):
                    collecting = True
                    continue

            if collecting:
                lines.append(line)

        return "\n".join(lines).strip()

    def _remove_commentary_lines(self, text: str) -> str:
        """Drop common LLaVA narration lines that leak into ad copy."""
        if not text:
            return ""

        commentary_prefixes = (
            "more details:",
            "additional context:",
            "additional details:",
            "analysis:",
            "interpretation:",
            "overall,",
            "overall ",
            "the ad ",
            "this ad ",
            "the image ",
            "this image ",
            "it shows",
            "it features",
            "it highlights",
        )

        cleaned_lines: list[str] = []
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            lowered = line.lower()
            if any(lowered.startswith(prefix) for prefix in commentary_prefixes):
                continue

            cleaned_lines.append(line)

        return "\n".join(cleaned_lines).strip()

    def _merge_results(self, deepseek_text: str, llava_analysis: str) -> VisionExtractionResult:
        """
        Merge results from both vision models.

        Strategy:
        - Use DeepSeek for primary text (better OCR)
        - Use LLaVA for context and validation
        - Combine both for maximum coverage
        """
        # Calculate confidence based on what we got
        confidence = 0.0

        if deepseek_text and llava_analysis:
            confidence = 0.95  # Both models succeeded
            method = "parallel"
        elif deepseek_text or llava_analysis:
            confidence = 0.70  # One model succeeded
            method = "fallback"
        else:
            confidence = 0.30  # Both failed
            method = "failed"

        # Merge text (prioritize DeepSeek for OCR)
        if deepseek_text:
            extracted_text = deepseek_text
            # Augment with LLaVA insights if available
            if llava_analysis and len(llava_analysis) > len(deepseek_text):
                extracted_text = f"{deepseek_text}\n\n{llava_analysis}"
        else:
            extracted_text = llava_analysis or "No text extracted"

        # Visual description from LLaVA
        visual_description = llava_analysis if llava_analysis else "No visual analysis available"

        return VisionExtractionResult(
            extracted_text=extracted_text,
            visual_description=visual_description,
            confidence=confidence,
            deepseek_text=deepseek_text,
            llava_analysis=llava_analysis,
            method_used=method,
            sections={},
        )

    def _create_fallback_result(self, error: str) -> VisionExtractionResult:
        """Create fallback result when vision fails."""
        return VisionExtractionResult(
            extracted_text=f"Vision extraction failed: {error}",
            visual_description="",
            confidence=0.0,
            deepseek_text="",
            llava_analysis="",
            method_used="failed",
            sections={},
        )


# ============================================================================
# STANDALONE TESTING
# ============================================================================

def test_vision_extraction():
    """Test the vision extractor on sample ads."""
    extractor = VisionExtractor()

    # Test with one of the downloaded screenshots
    test_image = "/Users/muhannadsaad/Desktop/ad-intelligence/test_screenshots/AR12079153035289296897/CR04376697774863810561.jpg"

    print("=" * 80)
    print("TESTING VISION EXTRACTION LAYER")
    print("=" * 80)
    print(f"\nTest image: {test_image}\n")

    result = extractor.extract(
        image_url="",  # Not needed if local_path is provided
        local_path=test_image
    )

    print("\n" + "=" * 80)
    print("EXTRACTION RESULTS:")
    print("=" * 80)
    print(f"\n📝 Extracted Text:")
    print(result.extracted_text)
    print(f"\n🎨 Visual Description:")
    print(result.visual_description)
    print(f"\n📊 Confidence: {result.confidence:.2f}")
    print(f"   Method: {result.method_used}")
    print("=" * 80)


if __name__ == "__main__":
    test_vision_extraction()
