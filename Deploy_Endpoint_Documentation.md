# /deploy Endpoint Documentation

## Overview

The `/deploy` endpoint allows you to deploy a ZIP file containing website files directly to Netlify. Each deployment creates a new Netlify site with a unique URL.

## Endpoint Details

**Method:** `POST`  
**URL:** `http://localhost:3001/deploy`  
**Content-Type:** `multipart/form-data`

## Authentication (Optional)

You can provide an API key for authentication in two ways:
- **Form field:** Include `api_key` in the form data
- **Header:** Include `X-API-Key` in request headers

## Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `zip_file` | File | Yes | ZIP file containing website files |
| `api_key` | String | No | API key for authentication |

## How It Works

1. **Receives ZIP file** via multipart form upload
2. **Extracts ZIP** to temporary directory
3. **Auto-renames** main HTML file to `index.html` if needed
4. **Creates new Netlify site** via API
5. **Generates file digests** (SHA1 hashes) for all files
6. **Creates deployment** with file manifest
7. **Uploads required files** efficiently
8. **Returns deployment URL** and metadata
9. **Cleans up** temporary files

## JavaScript Examples

### Basic Upload
```javascript
const deployToNetlify = async (zipFile) => {
  const formData = new FormData();
  formData.append('zip_file', zipFile);
  
  try {
    const response = await fetch('http://localhost:3001/deploy', {
      method: 'POST',
      body: formData
    });
    
    const result = await response.json();
    
    if (response.ok) {
      console.log('Deployment successful!');
      console.log('Site URL:', result.url);
      return result;
    } else {
      throw new Error(result.error);
    }
  } catch (error) {
    console.error('Deployment failed:', error);
    throw error;
  }
};

// Usage
const fileInput = document.getElementById('zipFileInput');
const file = fileInput.files[0];
deployToNetlify(file);
```

### With API Key Authentication
```javascript
const deployWithAuth = async (zipFile, apiKey) => {
  const formData = new FormData();
  formData.append('zip_file', zipFile);
  formData.append('api_key', apiKey);
  
  const response = await fetch('http://localhost:3001/deploy', {
    method: 'POST',
    body: formData
  });
  
  return await response.json();
};
```

### Using Headers for API Key
```javascript
const deployWithHeaderAuth = async (zipFile, apiKey) => {
  const formData = new FormData();
  formData.append('zip_file', zipFile);
  
  const response = await fetch('http://localhost:3001/deploy', {
    method: 'POST',
    headers: {
      'X-API-Key': apiKey
    },
    body: formData
  });
  
  return await response.json();
};
```

## HTML Form Example

```html
<form id="deployForm" enctype="multipart/form-data">
  <input type="file" name="zip_file" accept=".zip" required>
  <input type="text" name="api_key" placeholder="API Key (optional)">
  <button type="submit">Deploy to Netlify</button>
</form>

<script>
document.getElementById('deployForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  
  const formData = new FormData(e.target);
  
  try {
    const response = await fetch('http://localhost:3001/deploy', {
      method: 'POST',
      body: formData
    });
    
    const result = await response.json();
    
    if (response.ok) {
      alert(`Success! Site URL: ${result.url}`);
      window.open(result.url, '_blank');
    } else {
      alert(`Error: ${result.error}`);
    }
  } catch (error) {
    alert(`Network error: ${error.message}`);
  }
});
</script>
```

## cURL Example

```bash
# Basic deployment
curl -X POST \
  -F "zip_file=@website.zip" \
  http://localhost:3001/deploy

# With API key
curl -X POST \
  -F "zip_file=@website.zip" \
  -F "api_key=your_api_key_here" \
  http://localhost:3001/deploy

# With API key in header
curl -X POST \
  -H "X-API-Key: your_api_key_here" \
  -F "zip_file=@website.zip" \
  http://localhost:3001/deploy
```

## Response Format

### Success Response
```json
{
  "success": true,
  "message": "Deployment successful. Site is processing and will be live shortly.",
  "url": "https://amazing-site-123456.netlify.app",
  "site_id": "12345678-1234-1234-1234-123456789abc",
  "deploy_id": "deploy_123456789"
}
```

### Error Responses

**Missing ZIP file:**
```json
{
  "error": "No zip file provided"
}
```

**Invalid ZIP file:**
```json
{
  "error": "Invalid zip file provided"
}
```

**Authentication error:**
```json
{
  "error": "API key validation failed: Invalid API key"
}
```

**Server configuration error:**
```json
{
  "error": "Server is not configured for deployments."
}
```

**Netlify API error:**
```json
{
  "error": "Failed to deploy to Netlify.",
  "details": "Detailed error message from Netlify API"
}
```

## ZIP File Requirements

### Supported Files
- HTML files (`.html`, `.htm`)
- CSS files (`.css`)
- JavaScript files (`.js`)
- Images (`.jpg`, `.jpeg`, `.png`, `.gif`, `.svg`, `.webp`)
- Fonts (`.woff`, `.woff2`, `.ttf`, `.otf`)
- Other web assets

### File Structure
```
website.zip
├── index.html          # Main HTML file (auto-created if missing)
├── style.css           # CSS files
├── script.js           # JavaScript files
├── images/             # Image directory
│   ├── logo.png
│   └── background.jpg
└── assets/             # Other assets
    └── fonts/
        └── custom.woff2
```

### Important Notes
- **Maximum files:** 25,000 files per ZIP
- **Main HTML file:** Will be automatically renamed to `index.html` if needed
- **File paths:** Relative paths are preserved
- **Each deployment:** Creates a new Netlify site (new URL each time)

## Error Handling Best Practices

```javascript
const handleDeployment = async (zipFile, apiKey = null) => {
  try {
    // Validate file before upload
    if (!zipFile) {
      throw new Error('Please select a ZIP file');
    }
    
    if (!zipFile.name.toLowerCase().endsWith('.zip')) {
      throw new Error('Please select a valid ZIP file');
    }
    
    if (zipFile.size > 50 * 1024 * 1024) { // 50MB limit
      throw new Error('ZIP file is too large (max 50MB)');
    }
    
    // Show loading state
    const loadingElement = document.getElementById('loading');
    loadingElement.style.display = 'block';
    
    const result = await deployToNetlify(zipFile, apiKey);
    
    // Handle success
    console.log('Deployment successful:', result);
    showSuccess(`Site deployed successfully! URL: ${result.url}`);
    
    return result;
    
  } catch (error) {
    // Handle different error types
    if (error.message.includes('API key')) {
      showError('Authentication failed. Please check your API key.');
    } else if (error.message.includes('zip')) {
      showError('Invalid ZIP file. Please check your file and try again.');
    } else if (error.message.includes('Network')) {
      showError('Network error. Please check your connection and try again.');
    } else {
      showError(`Deployment failed: ${error.message}`);
    }
    
    throw error;
  } finally {
    // Hide loading state
    const loadingElement = document.getElementById('loading');
    loadingElement.style.display = 'none';
  }
};
```

## Complete Working Example

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Netlify Deployment</title>
    <style>
        .container { max-width: 600px; margin: 50px auto; padding: 20px; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input[type="file"], input[type="text"] { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
        button { background: #0066cc; color: white; padding: 12px 24px; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background: #0052a3; }
        button:disabled { background: #ccc; cursor: not-allowed; }
        .result { margin-top: 20px; padding: 15px; border-radius: 4px; }
        .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .loading { display: none; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Deploy to Netlify</h1>
        
        <form id="deployForm">
            <div class="form-group">
                <label for="zipFile">Select ZIP File:</label>
                <input type="file" id="zipFile" accept=".zip" required>
            </div>
            
            <div class="form-group">
                <label for="apiKey">API Key (optional):</label>
                <input type="text" id="apiKey" placeholder="Enter your API key">
            </div>
            
            <button type="submit" id="deployBtn">Deploy to Netlify</button>
        </form>
        
        <div id="loading" class="loading">
            <p>Deploying your site... Please wait.</p>
        </div>
        
        <div id="result"></div>
    </div>

    <script>
        document.getElementById('deployForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const zipFile = document.getElementById('zipFile').files[0];
            const apiKey = document.getElementById('apiKey').value;
            const resultDiv = document.getElementById('result');
            const loadingDiv = document.getElementById('loading');
            const deployBtn = document.getElementById('deployBtn');
            
            // Clear previous results
            resultDiv.innerHTML = '';
            
            // Validate input
            if (!zipFile) {
                showResult('Please select a ZIP file', 'error');
                return;
            }
            
            // Show loading state
            loadingDiv.style.display = 'block';
            deployBtn.disabled = true;
            deployBtn.textContent = 'Deploying...';
            
            try {
                const formData = new FormData();
                formData.append('zip_file', zipFile);
                if (apiKey) {
                    formData.append('api_key', apiKey);
                }
                
                const response = await fetch('http://localhost:3001/deploy', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    showResult(`
                        <strong>Deployment Successful!</strong><br>
                        <strong>Site URL:</strong> <a href="${result.url}" target="_blank">${result.url}</a><br>
                        <strong>Site ID:</strong> ${result.site_id}<br>
                        <strong>Deploy ID:</strong> ${result.deploy_id}
                    `, 'success');
                } else {
                    showResult(`Deployment failed: ${result.error}`, 'error');
                }
                
            } catch (error) {
                showResult(`Network error: ${error.message}`, 'error');
            } finally {
                // Hide loading state
                loadingDiv.style.display = 'none';
                deployBtn.disabled = false;
                deployBtn.textContent = 'Deploy to Netlify';
            }
        });
        
        function showResult(message, type) {
            const resultDiv = document.getElementById('result');
            resultDiv.innerHTML = message;
            resultDiv.className = `result ${type}`;
        }
    </script>
</body>
</html>
```

This endpoint provides a simple and efficient way to deploy static websites to Netlify directly from your frontend application.