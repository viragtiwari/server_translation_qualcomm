# Frontend Guide: Deploying a Site with the `/deploy` Endpoint

This guide explains how to use the `/deploy` endpoint from your frontend application to upload and deploy a zipped website.

## Endpoint Details

*   **URL**: `/deploy`
*   **Method**: `POST`
*   **Headers**: The request will be a `multipart/form-data` request. You don't need to set the `Content-Type` header manually when using `FormData` with `fetch`; the browser will do it for you.

## Request Body

The body of the request must be a `FormData` object containing the zip file of your site.

*   **Field Name**: `zip_file`
*   **Value**: The zip file to be uploaded.

## JavaScript Example using `fetch`

Here is an example of how to use the `fetch` API to send the deployment request from a frontend application. This code assumes you have an HTML file input element (`<input type="file">`) that the user interacts with to select the zip file.

```html
<!-- In your HTML file -->
<input type="file" id="zipFileInput" accept=".zip">
<button id="deployButton">Deploy Site</button>
```

```javascript
// In your JavaScript file
document.addEventListener('DOMContentLoaded', () => {
    const zipFileInput = document.getElementById('zipFileInput');
    const deployButton = document.getElementById('deployButton');

    deployButton.addEventListener('click', () => {
        const file = zipFileInput.files[0];

        if (!file) {
            alert('Please select a zip file to deploy.');
            return;
        }

        const formData = new FormData();
        formData.append('zip_file', file);

        // The server runs on port 3001 by default.
        // Replace with your actual server URL if it's different.
        const serverUrl = 'http://localhost:3001/deploy'; 

        fetch(serverUrl, {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                // Try to get more detailed error from the response body
                return response.json().then(errorData => {
                    throw new Error(`Deployment failed: ${errorData.error || response.statusText}`);
                });
            }
            return response.json();
        })
        .then(data => {
            console.log('Deployment successful:', data);
            alert(`Site deployed successfully! Check server logs for details.`);
        })
        .catch(error => {
            console.error('Error during deployment:', error);
            alert(error.message);
        });
    });
});
```

### How the Example Works

1.  **File Selection**: The user selects a zip file using the file input.
2.  **FormData**: When the "Deploy Site" button is clicked, a `FormData` object is created, and the selected file is appended to it with the key `zip_file`.
3.  **Fetch Request**: A `POST` request is sent to the `/deploy` endpoint with the `FormData` object as the body. The browser automatically sets the correct `Content-Type` header for `multipart/form-data`.
4.  **Response Handling**: The code then handles the JSON response from the server, showing a success message or an error message if the deployment fails. The specific details of the deployment (like the new site URL) will be in the server's response and can be accessed from the `data` object in the success handler.