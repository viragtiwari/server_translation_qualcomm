import os
import logging
from sarvamai import SarvamAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# Initialize client with API key from environment variables
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
if not SARVAM_API_KEY:
    raise Exception("FATAL ERROR: SARVAM_API_KEY is not defined in .env file.")

client = SarvamAI(
    api_subscription_key=SARVAM_API_KEY,
)

def language_translate(text: str, target_language: str = "en-IN") -> str:
    """
    Translates text from auto-detected language to a target language.
    
    Args:
        text (str): Text to translate.
        target_language (str): The target language code (e.g., "en-IN", "hi").
                               Defaults to "en-IN".
        
    Returns:
        str: Translated text.
        
    Raises:
        ValueError: If text is empty or None.
        Exception: If translation service fails.
    """
    # Input validation
    if not text or not isinstance(text, str) or not text.strip():
        print("Invalid input: text is empty or not a string", flush=True)
        raise ValueError("Text must be a non-empty string")
    
    # Ensure the target language code is in the correct format (e.g., 'hi-IN')
    if "-" not in target_language:
        target_language = f"{target_language}-IN"
    
    try:
        # First detect the source language
        source_language = detect_language(text)
        if "-" not in source_language:
            source_language = f"{source_language}-IN"
            
        print(f"Attempting translation for text of length: {len(text)} from {source_language} to {target_language}", flush=True)
        
        response = client.text.translate(
            input=text,
            source_language_code=source_language,
            target_language_code=target_language,
            model="sarvam-translate:v1",
        )
        
        if not response or not hasattr(response, 'translated_text'):
            print("Invalid response from translation service", flush=True)
            raise Exception("Translation service returned invalid response")
        
        translated_text = response.translated_text
        
        if not translated_text or not isinstance(translated_text, str):
            print("Translation service returned empty or invalid result", flush=True)
            raise Exception("Translation service returned empty result")
        
        print("Translation completed successfully", flush=True)
        return translated_text
        
    except ValueError:
        raise
    except Exception as e:
        print(f"Translation failed: {str(e)}", flush=True)
        raise Exception(f"Translation service error: {str(e)}")

def detect_language(text: str) -> str:
    """
    Detects the language of the input text.

    Args:
        text (str): The text to analyze.

    Returns:
        str: The detected language code (e.g., "en", "hi").

    Raises:
        ValueError: If text is empty or None.
        Exception: If the language detection service fails.
    """
    if not text or not isinstance(text, str) or not text.strip():
        print("Invalid input for language detection: text is empty or not a string", flush=True)
        raise ValueError("Text must be a non-empty string")

    try:
        print(f"Attempting to detect language for text of length: {len(text)}", flush=True)
        response = client.text.identify_language(input=text)

        if not response or not hasattr(response, 'language_code'):
            print("Invalid response from language detection service", flush=True)
            raise Exception("Language detection service returned an invalid response")

        language_code = response.language_code
        print(f"Successfully detected language: {language_code}", flush=True)
        return language_code

    except ValueError:
        raise
    except Exception as e:
        print(f"Language detection failed: {str(e)}", flush=True)
        raise Exception(f"Language detection service error: {str(e)}")


# Production-ready health check for the translation service
def check_translation_service_health() -> bool:
    """
    Checks if the translation service is working properly
    
    Returns:
        bool: True if service is healthy, False otherwise
    """
    try:
        # Test with a simple phrase
        test_result = language_translate("Hello")
        return bool(test_result and len(test_result.strip()) > 0)
    except Exception as e:
        print(f"Translation service health check failed: {e}", flush=True)
        return False


# Keep the original test commented out for reference
# print(language_translate("Haan bhai kya haal hai??"))
