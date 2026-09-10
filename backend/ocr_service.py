import os
import io
import json
from google.cloud import vision
from google.oauth2 import service_account
from google.api_core.exceptions import GoogleAPIError

# We only have the API Key. The google-cloud-vision library typically uses service accounts,
# but we can use the API key by passing it via client_options.
from google.api_core.client_options import ClientOptions

import pytesseract
from PIL import Image
import logging

logger = logging.getLogger(__name__)

class OCRService:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_CLOUD_VISION_API_KEY")
        if self.api_key:
            client_options = ClientOptions(api_key=self.api_key)
            self.vision_client = vision.ImageAnnotatorClient(client_options=client_options)
        else:
            self.vision_client = None
            logger.warning("Google Cloud Vision API key not found. Will use fallback OCR.")

    def extract_text(self, image_bytes: bytes) -> str:
        """Extracts text from image using Google Vision API with Tesseract fallback."""
        if self.vision_client:
            try:
                logger.info("Attempting OCR with Google Cloud Vision...")
                image = vision.Image(content=image_bytes)
                response = self.vision_client.document_text_detection(image=image)
                if response.error.message:
                    raise Exception(f"{response.error.message}")
                return response.full_text_annotation.text
            except Exception as e:
                logger.error(f"Google Vision API failed: {e}. Falling back to Tesseract.")
                return self._fallback_ocr(image_bytes)
        else:
            return self._fallback_ocr(image_bytes)

    def _fallback_ocr(self, image_bytes: bytes) -> str:
        """Fallback OCR using Tesseract."""
        logger.info("Using Tesseract for OCR...")
        try:
            image = Image.open(io.BytesIO(image_bytes))
            text = pytesseract.image_to_string(image)
            return text
        except Exception as e:
            logger.error(f"Tesseract OCR failed: {e}")
            return ""

ocr_service = OCRService()
