import os
import logging
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from dotenv import load_dotenv
import gc
import time

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CRITICAL: Set environment variables BEFORE importing transformers
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Language code mapping for Sarvam-Translate
LANGUAGE_MAP = {
    "as": "Assamese", "as-IN": "Assamese",
    "bn": "Bengali", "bn-IN": "Bengali",
    "brx": "Bodo", "brx-IN": "Bodo",
    "doi": "Dogri", "doi-IN": "Dogri",
    "gu": "Gujarati", "gu-IN": "Gujarati",
    "en": "English", "en-IN": "English",
    "hi": "Hindi", "hi-IN": "Hindi",
    "kn": "Kannada", "kn-IN": "Kannada",
    "ks": "Kashmiri", "ks-IN": "Kashmiri",
    "kok": "Konkani", "kok-IN": "Konkani",
    "mai": "Maithili", "mai-IN": "Maithili",
    "ml": "Malayalam", "ml-IN": "Malayalam",
    "mni": "Manipuri", "mni-IN": "Manipuri",
    "mr": "Marathi", "mr-IN": "Marathi",
    "ne": "Nepali", "ne-IN": "Nepali",
    "or": "Odia", "or-IN": "Odia",
    "pa": "Punjabi", "pa-IN": "Punjabi",
    "sa": "Sanskrit", "sa-IN": "Sanskrit",
    "sat": "Santali", "sat-IN": "Santali",
    "sd": "Sindhi", "sd-IN": "Sindhi",
    "ta": "Tamil", "ta-IN": "Tamil",
    "te": "Telugu", "te-IN": "Telugu",
    "ur": "Urdu", "ur-IN": "Urdu"
}

# Reverse mapping for language detection
REVERSE_LANGUAGE_MAP = {v.lower(): k for k, v in LANGUAGE_MAP.items() if "-IN" not in k}

# Model configuration
MODEL_NAME = "sarvamai/sarvam-translate"
model = None
tokenizer = None

def initialize_model():
    """
    Initialize the Sarvam-Translate model and tokenizer.
    This is called lazily on first use to avoid loading the model at import time.
    """
    global model, tokenizer
    
    if model is None or tokenizer is None:
        try:
            print("=" * 60, flush=True)
            print("Loading Sarvam-Translate model...", flush=True)
            print("=" * 60, flush=True)
            
            # Clear memory first
            gc.collect()
            
            # Determine device
            device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"Device: {device}", flush=True)
            print(f"PyTorch version: {torch.__version__}", flush=True)
            
            if device == "cpu":
                print("⚠️  Running on CPU - translations will be slow", flush=True)
            
            # Step 1: Load tokenizer
            print("\n[1/3] Loading tokenizer...", flush=True)
            try:
                tokenizer = AutoTokenizer.from_pretrained(
                    MODEL_NAME,
                    trust_remote_code=True,
                    local_files_only=False
                )
                print("✓ Tokenizer loaded", flush=True)
            except Exception as e:
                print(f"❌ Tokenizer loading failed: {e}", flush=True)
                raise
            
            # Step 2: Download model files if needed
            print("\n[2/3] Preparing model files...", flush=True)
            print("      (First run: downloading ~8GB, this takes time)", flush=True)
            
            # Step 3: Load model with safeguards
            print("\n[3/3] Loading model into memory...", flush=True)
            print("      This step loads 2 checkpoint shards sequentially", flush=True)
            print("      Expected time: 5-15 minutes on ARM CPU", flush=True)
            print("      ⏳ Please wait - do not interrupt!\n", flush=True)
            
            start_time = time.time()
            
            try:
                if device == "cpu":
                    # Use the most conservative loading approach for CPU
                    # Note: Some transformers versions use 'dtype' instead of 'torch_dtype'
                    try:
                        model = AutoModelForCausalLM.from_pretrained(
                            MODEL_NAME,
                            dtype=torch.float32,  # Newer transformers versions
                            low_cpu_mem_usage=True,
                            trust_remote_code=True,
                            device_map=None,
                            local_files_only=False,
                        )
                    except TypeError:
                        # Fallback for older transformers versions
                        model = AutoModelForCausalLM.from_pretrained(
                            MODEL_NAME,
                            torch_dtype=torch.float32,
                            low_cpu_mem_usage=True,
                            trust_remote_code=True,
                            device_map=None,
                            local_files_only=False,
                        )
                    
                    print("\n✓ Model checkpoint loaded!", flush=True)
                    print("   Moving to CPU device...", flush=True)
                    
                    # Explicitly move to CPU
                    model = model.to('cpu')
                    
                    # Set to eval mode
                    model.eval()
                    
                    # Disable gradients
                    for param in model.parameters():
                        param.requires_grad = False
                    
                else:
                    # GPU loading
                    model = AutoModelForCausalLM.from_pretrained(
                        MODEL_NAME,
                        torch_dtype=torch.bfloat16,
                        low_cpu_mem_usage=True,
                        trust_remote_code=True,
                        device_map="auto",
                    )
                
                elapsed = time.time() - start_time
                print(f"\n✓ Model fully loaded in {elapsed:.1f} seconds", flush=True)
                
            except Exception as load_error:
                print(f"\n❌ Model loading failed!", flush=True)
                print(f"Error: {load_error}", flush=True)
                print(f"Error type: {type(load_error).__name__}", flush=True)
                raise
            
            # Clear memory
            gc.collect()
            
            # Calculate model size
            try:
                param_count = sum(p.numel() for p in model.parameters()) / 1e9
                print(f"Model parameters: {param_count:.2f}B", flush=True)
            except:
                pass
            
            print("=" * 60, flush=True)
            print("✓ Initialization complete - ready to translate!", flush=True)
            print("=" * 60, flush=True)
            
        except KeyboardInterrupt:
            print("\n\n❌ Loading interrupted by user", flush=True)
            model = None
            tokenizer = None
            gc.collect()
            raise
            
        except Exception as e:
            print(f"\n❌ FATAL ERROR during initialization", flush=True)
            print(f"Error: {str(e)}", flush=True)
            print(f"Type: {type(e).__name__}", flush=True)
            
            # Full traceback
            import traceback
            print("\nFull traceback:", flush=True)
            traceback.print_exc()
            
            # Cleanup
            model = None
            tokenizer = None
            gc.collect()
            
            raise Exception(f"Model initialization failed: {str(e)}")

def get_language_name(language_code: str) -> str:
    """Convert language code to full language name."""
    if language_code in LANGUAGE_MAP:
        return LANGUAGE_MAP[language_code]
    
    base_code = language_code.split("-")[0]
    if base_code in LANGUAGE_MAP:
        return LANGUAGE_MAP[base_code]
    
    print(f"Warning: Unknown language '{language_code}', using English", flush=True)
    return "English"

def language_translate(text: str, target_language: str = "en-IN") -> str:
    """
    Translates text from auto-detected language to a target language.
    
    Args:
        text (str): Text to translate.
        target_language (str): Target language code (e.g., "en-IN", "hi").
        
    Returns:
        str: Translated text.
    """
    if not text or not isinstance(text, str) or not text.strip():
        raise ValueError("Text must be a non-empty string")
    
    if "-" not in target_language:
        target_language = f"{target_language}-IN"
    
    try:
        # Initialize model if needed
        if model is None or tokenizer is None:
            initialize_model()
        
        target_lang_name = get_language_name(target_language)
        
        print(f"\nTranslating to {target_lang_name}...", flush=True)
        
        # Create prompt
        messages = [
            {"role": "system", "content": f"Translate the text below to {target_lang_name}."},
            {"role": "user", "content": text}
        ]
        
        prompt_text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        # Tokenize
        model_inputs = tokenizer([prompt_text], return_tensors="pt").to(model.device)
        
        print("   Generating... (10-30 seconds on CPU)", flush=True)
        start_time = time.time()
        
        # Generate translation
        with torch.no_grad():
            generated_ids = model.generate(
                **model_inputs,
                max_new_tokens=1024,
                do_sample=True,
                temperature=0.01,
                num_return_sequences=1,
                pad_token_id=tokenizer.eos_token_id,
                use_cache=True
            )
        
        elapsed = time.time() - start_time
        
        # Decode
        output_ids = generated_ids[0][len(model_inputs.input_ids[0]):].tolist()
        translated_text = tokenizer.decode(output_ids, skip_special_tokens=True)
        
        # Cleanup
        del model_inputs, generated_ids, output_ids
        gc.collect()
        
        if not translated_text or not isinstance(translated_text, str):
            raise Exception("Translation returned empty result")
        
        print(f"✓ Done in {elapsed:.1f}s", flush=True)
        return translated_text.strip()
        
    except Exception as e:
        print(f"❌ Translation failed: {str(e)}", flush=True)
        raise Exception(f"Translation error: {str(e)}")

def detect_language(text: str) -> str:
    """Detect the language of input text."""
    if not text or not isinstance(text, str) or not text.strip():
        raise ValueError("Text must be a non-empty string")

    try:
        if model is None or tokenizer is None:
            initialize_model()
        
        messages = [
            {"role": "system", "content": "Identify the language of the following text. Respond with only the language name."},
            {"role": "user", "content": text[:500]}
        ]
        
        prompt_text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        model_inputs = tokenizer([prompt_text], return_tensors="pt").to(model.device)
        
        with torch.no_grad():
            generated_ids = model.generate(
                **model_inputs,
                max_new_tokens=50,
                do_sample=True,
                temperature=0.01,
                num_return_sequences=1,
                pad_token_id=tokenizer.eos_token_id
            )
        
        output_ids = generated_ids[0][len(model_inputs.input_ids[0]):].tolist()
        detected_name = tokenizer.decode(output_ids, skip_special_tokens=True).strip()
        
        del model_inputs, generated_ids, output_ids
        gc.collect()
        
        language_code = REVERSE_LANGUAGE_MAP.get(detected_name.lower(), "en")
        print(f"Detected: {language_code} ({detected_name})", flush=True)
        return language_code

    except Exception as e:
        print(f"Language detection failed: {e}, defaulting to English", flush=True)
        return "en"

def check_translation_service_health() -> bool:
    """Check if translation service is working."""
    try:
        initialize_model()
        result = language_translate("Hello", target_language="hi")
        return bool(result and len(result.strip()) > 0)
    except Exception as e:
        print(f"Health check failed: {e}", flush=True)
        return False

def quick_test():
    """Quick test of translation service."""
    print("\n" + "=" * 60)
    print("QUICK TEST")
    print("=" * 60)
    
    tests = [
        ("Hello, how are you?", "hi"),
        ("Good morning", "ta"),
    ]
    
    for text, lang in tests:
        print(f"\n'{text}' -> {get_language_name(lang)}")
        try:
            result = language_translate(text, lang)
            print(f"Result: {result}")
        except Exception as e:
            print(f"Failed: {e}")

# Uncomment to test
if __name__ == "__main__":
    quick_test()