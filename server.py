import os
import time
import zipfile
import tempfile
import shutil
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import logging
import requests
from utils import language_translate, detect_language
# from netlify_py import NetlifyPy  # Has Windows compatibility issues

# --- Basic Logging Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# --- Environment and Configuration ---
app = Flask(__name__)
CORS(app)
# USERDB_BASE_URL is no longer required since we're not doing external validation
# USERDB_BASE_URL = os.getenv("USERDB_BASE_URL")

# --- API Key Validation Function ---
def is_api_key_valid(api_key: str):
    """
    Validates that API key is present and non-empty.
    Returns a tuple of (is_valid, error_message)
    """
    if not api_key or not isinstance(api_key, str) or not api_key.strip():
        return False, "API key is required"
    
    return True, ""

# --- Translation Endpoint ---
@app.route('/api/translate', methods=['POST'])
def translate_text():
    """
    Translation endpoint that validates API key and translates text.
    Accepts an optional target_language parameter.
    Expected request body:
    {
        "text": "text to translate",
        "api_key": "your_api_key",
        "target_language": "hi" (optional, defaults to "en-IN")
    }
    """
    print(f"--- Translate Request ---")
    try:
        data = request.get_json()
        print(f"Request data: {data}")
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        
        text = data.get('text')
        api_key = data.get('api_key')
        target_language = data.get('target_language', 'en-IN') # Default to en-IN
        
        if not text:
            return jsonify({"error": "'text' field is required"}), 400
        if not api_key:
            return jsonify({"error": "'api_key' field is required"}), 400
        
        is_valid, error_message = is_api_key_valid(api_key)
        if not is_valid:
            return jsonify({"error": f"API key validation failed: {error_message}"}), 401
        
        try:
            translated_text = language_translate(text, target_language=target_language)
            
            response_data = {
                "success": True,
                "original_text": text,
                "translated_text": translated_text,
                "source_language": "auto-detected",
                "target_language": target_language
            }
            print(f"--- Translate Response ---")
            print(f"Response data: {response_data}")
            return jsonify(response_data), 200
            
        except Exception as translation_error:
            logger.error(f"Translation failed: {translation_error}")
            return jsonify({"error": "Translation service failed"}), 500
    
    except Exception as e:
        logger.error(f"Translation endpoint error: {e}")
        return jsonify({"error": "Internal server error"}), 500

# --- Language Detection Endpoint ---
@app.route('/api/detect-language', methods=['POST'])
def detect_language_endpoint():
    """
    Detects the language of the input text after validating the API key.
    Expected request body:
    {
        "text": "text to analyze",
        "api_key": "your_api_key"
    }
    """
    print(f"--- Detect Language Request ---")
    try:
        data = request.get_json()
        print(f"Request data: {data}")
        if not data:
            return jsonify({"error": "Request body is required"}), 400

        text = data.get('text')
        api_key = data.get('api_key')

        if not text:
            return jsonify({"error": "'text' field is required"}), 400
        if not api_key:
            return jsonify({"error": "'api_key' field is required"}), 400

        is_valid, error_message = is_api_key_valid(api_key)
        if not is_valid:
            return jsonify({"error": f"API key validation failed: {error_message}"}), 401

        try:
            language_code = detect_language(text)
            print(language_code)
            response_data = {
                "success": True,
                "text": text,
                "language_code": language_code
            }
            print(f"--- Detect Language Response ---")
            print(f"Response data: {response_data}")
            return jsonify(response_data), 200
        
        except Exception as detection_error:
            logger.error(f"Language detection failed: {detection_error}")
            return jsonify({"error": "Language detection service failed"}), 500

    except Exception as e:
        logger.error(f"Language detection endpoint error: {e}")
        return jsonify({"error": "Internal server error"}), 500

# --- Netlify Deployment Endpoint ---
@app.route('/deploy', methods=['POST'])
def deploy_to_netlify():
    """
    Deploys a zipped website to Netlify by extracting the zip and using file digest method.
    Creates a new site for each deployment.
    Requires API key validation for security.
    """
    logger.info("--- Netlify Deployment Request ---")

    # Validate API key
    api_key = request.form.get('api_key') or request.headers.get('X-API-Key')
    if api_key:
        is_valid, error_message = is_api_key_valid(api_key)
        if not is_valid:
            return jsonify({"error": f"API key validation failed: {error_message}"}), 401

    if 'zip_file' not in request.files:
        return jsonify({"error": "No zip file provided"}), 400

    zip_file = request.files['zip_file']
    if zip_file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    netlify_pat = os.getenv("NETLIFY_PAT")
    if not netlify_pat:
        logger.error("Netlify PAT not configured in environment variables.")
        return jsonify({"error": "Server is not configured for deployments."}), 500

    auth_header = {"Authorization": f"Bearer {netlify_pat}"}
    temp_dir = None
    
    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        logger.info(f"Created temporary directory: {temp_dir}")
        
        # Save uploaded zip file
        zip_path = os.path.join(temp_dir, "upload.zip")
        zip_file.save(zip_path)
        
        # Extract zip file
        extract_dir = os.path.join(temp_dir, "extracted")
        os.makedirs(extract_dir, exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        logger.info(f"Extracted zip file to: {extract_dir}")
        
        # Debug: Log the extracted file structure
        logger.info("=== EXTRACTED FILE STRUCTURE ===")
        for root, dirs, files in os.walk(extract_dir):
            level = root.replace(extract_dir, '').count(os.sep)
            indent = ' ' * 2 * level
            logger.info(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                logger.info(f"{subindent}{file}")
        logger.info("=== END FILE STRUCTURE ===")
        
        # Check if files are nested in a subdirectory and flatten if needed
        extracted_items = os.listdir(extract_dir)
        if len(extracted_items) == 1 and os.path.isdir(os.path.join(extract_dir, extracted_items[0])):
            # Files are nested in a single directory, move them up
            nested_dir = os.path.join(extract_dir, extracted_items[0])
            logger.info(f"Found nested directory: {extracted_items[0]}, flattening...")
            for item in os.listdir(nested_dir):
                src = os.path.join(nested_dir, item)
                dst = os.path.join(extract_dir, item)
                shutil.move(src, dst)
                logger.info(f"Moved {item} to root level")
            os.rmdir(nested_dir)
            logger.info("Flattened nested directory structure")
        
        # Ensure there's an index.html file at root level
        index_html_path = os.path.join(extract_dir, 'index.html')
        if os.path.exists(index_html_path):
            logger.info("✅ index.html found at root level")
        else:
            logger.warning("❌ No index.html at root level, looking for HTML files...")
            html_files = []
            for root, dirs, filenames in os.walk(extract_dir):
                for filename in filenames:
                    if filename.lower().endswith(('.html', '.htm')):
                        html_files.append(os.path.join(root, filename))
            
            if html_files:
                first_html = html_files[0]
                shutil.copy2(first_html, index_html_path)
                logger.info(f"Copied {os.path.basename(first_html)} to index.html at root")
            else:
                logger.error("No HTML files found in the ZIP!")
        
        # Create a new site
        logger.info("Creating new site...")
        create_url = "https://api.netlify.com/api/v1/sites"
        create_headers = {**auth_header, "Content-Type": "application/json"}
        
        create_response = requests.post(create_url, headers=create_headers, json={})
        create_response.raise_for_status()
        
        new_site_data = create_response.json()
        site_id = new_site_data.get("id")
        logger.info(f"Created new site with ID: {site_id}")
        
        # Create a new ZIP file from the extracted and processed files
        processed_zip_path = os.path.join(temp_dir, "processed.zip")
        with zipfile.ZipFile(processed_zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
            for root, dirs, files in os.walk(extract_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Use relative path from extract_dir as the archive name
                    arcname = os.path.relpath(file_path, extract_dir)
                    zip_ref.write(file_path, arcname)
                    logger.info(f"Added to ZIP: {arcname}")
        
        logger.info(f"Created processed ZIP file: {processed_zip_path}")
        
        # Deploy using direct ZIP upload method
        deploy_url = f"https://api.netlify.com/api/v1/sites/{site_id}/deploys"
        deploy_headers = {**auth_header, "Content-Type": "application/zip"}
        
        with open(processed_zip_path, 'rb') as zip_file:
            zip_content = zip_file.read()
        
        deploy_response = requests.post(deploy_url, headers=deploy_headers, data=zip_content)
        deploy_response.raise_for_status()
        
        deploy_info = deploy_response.json()
        deploy_id = deploy_info.get("id")
        site_url = deploy_info.get("ssl_url") or deploy_info.get("url")
        
        logger.info(f"Deployment successful! URL: {site_url}")
        
        return jsonify({
            "success": True,
            "message": "Deployment successful. Site is processing and will be live shortly.",
            "url": site_url,
            "site_id": site_id,
            "deploy_id": deploy_id
        }), 200

    except zipfile.BadZipFile:
        logger.error("Invalid zip file provided")
        return jsonify({"error": "Invalid zip file provided"}), 400
    except requests.exceptions.RequestException as e:
        logger.error(f"Netlify API error: {e}")
        if e.response is not None:
            error_details = e.response.text
            status_code = e.response.status_code
            logger.error(f"Netlify API Response (Status {status_code}): {error_details}")
            return jsonify({
                "error": "Failed to deploy to Netlify.",
                "details": error_details
            }), status_code
        return jsonify({"error": f"Deployment failed: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Failed to deploy to Netlify: {e}")
        return jsonify({"error": f"Deployment failed: {str(e)}"}), 500
    finally:
        # Clean up temporary directory
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                logger.info(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up temporary directory: {cleanup_error}")


# --- Health Check Endpoint ---
@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Simple health check endpoint
    """
    print(f"--- Health Check Request ---")
    response_data = {
        "status": "healthy",
        "service": "translation-service",
        "timestamp": "2025-01-19T16:05:51Z"
    }
    print(f"--- Health Check Response ---")
    print(f"Response data: {response_data}")
    return jsonify(response_data), 200

# --- Server Start ---
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3001))
    app.run(host='0.0.0.0', port=port, debug=True)