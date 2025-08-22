from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import StreamingResponse, JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from rembg import remove
from PIL import Image
import io
import base64
from typing import Optional
import uuid
from datetime import datetime
import uvicorn
import os

app = FastAPI(title="Background Remover API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

def validate_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# HTML interface embedded in the code
HTML_INTERFACE = """
<!DOCTYPE html>
<html>
<head>
    <title>BG Remover API</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 40px;
            max-width: 900px;
            width: 100%;
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2em;
        }
        .upload-area {
            border: 3px dashed #667eea;
            border-radius: 15px;
            padding: 40px;
            text-align: center;
            transition: all 0.3s ease;
            cursor: pointer;
            background: #f8f9ff;
        }
        .upload-area:hover {
            border-color: #764ba2;
            background: #f0f2ff;
        }
        .upload-area.dragover {
            border-color: #764ba2;
            background: #e8ebff;
        }
        input[type="file"] {
            display: none;
        }
        .upload-label {
            display: inline-block;
            cursor: pointer;
            color: #667eea;
            font-weight: 600;
            font-size: 1.1em;
        }
        .upload-icon {
            font-size: 3em;
            margin-bottom: 10px;
        }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 40px;
            border-radius: 50px;
            font-size: 1.1em;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
            margin: 20px auto;
            display: block;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }
        button:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
        }
        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        .result {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-top: 30px;
        }
        .image-box {
            text-align: center;
        }
        .image-box h3 {
            color: #555;
            margin-bottom: 15px;
            font-size: 1.1em;
        }
        .image-container {
            position: relative;
            background: #f5f5f5;
            border-radius: 10px;
            overflow: hidden;
            min-height: 200px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        img {
            max-width: 100%;
            height: auto;
            display: block;
            border-radius: 10px;
        }
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
        }
        .loading.active {
            display: block;
        }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 15px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .download-btn {
            background: #4caf50;
            padding: 10px 25px;
            font-size: 0.9em;
            margin-top: 15px;
            display: none;
        }
        .download-btn.show {
            display: inline-block;
        }
        .api-info {
            background: #f8f9ff;
            border-radius: 10px;
            padding: 20px;
            margin-top: 30px;
        }
        .api-info h3 {
            color: #333;
            margin-bottom: 10px;
        }
        .endpoint {
            background: white;
            padding: 10px;
            border-radius: 5px;
            margin: 5px 0;
            font-family: monospace;
            color: #667eea;
        }
        @media (max-width: 768px) {
            .result {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎨 Background Remover API</h1>
        
        <div class="upload-area" id="uploadArea">
            <div class="upload-icon">📸</div>
            <label for="fileInput" class="upload-label">
                Choose an image or drag & drop here
            </label>
            <input type="file" id="fileInput" accept="image/*">
            <p style="color: #999; margin-top: 10px;">PNG, JPG, JPEG, WEBP (Max 16MB)</p>
        </div>
        
        <button id="processBtn" onclick="removeBackground()" disabled>
            Remove Background
        </button>
        
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p>Processing your image... This may take a moment.</p>
        </div>
        
        <div class="result" id="result" style="display: none;">
            <div class="image-box">
                <h3>Original Image</h3>
                <div class="image-container">
                    <img id="originalImage" />
                </div>
            </div>
            <div class="image-box">
                <h3>Background Removed</h3>
                <div class="image-container">
                    <img id="processedImage" />
                </div>
                <button class="download-btn" id="downloadBtn" onclick="downloadImage()">
                    Download Result
                </button>
            </div>
        </div>
        
        <div class="api-info">
            <h3>API Endpoints</h3>
            <div class="endpoint">POST /remove-bg - Remove background from uploaded image</div>
            <div class="endpoint">POST /remove-bg-url - Remove background from image URL</div>
            <div class="endpoint">GET /docs - Interactive API documentation</div>
        </div>
    </div>

    <script>
        let processedImageData = null;
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const processBtn = document.getElementById('processBtn');
        
        // Drag and drop functionality
        uploadArea.addEventListener('click', () => fileInput.click());
        
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                fileInput.files = files;
                handleFileSelect();
            }
        });
        
        fileInput.addEventListener('change', handleFileSelect);
        
        function handleFileSelect() {
            const file = fileInput.files[0];
            if (file) {
                if (file.size > 16 * 1024 * 1024) {
                    alert('File size exceeds 16MB limit');
                    return;
                }
                const reader = new FileReader();
                reader.onload = function(e) {
                    document.getElementById('originalImage').src = e.target.result;
                    document.getElementById('result').style.display = 'grid';
                    processBtn.disabled = false;
                }
                reader.readAsDataURL(file);
            }
        }
        
        async function removeBackground() {
            const file = fileInput.files[0];
            if (!file) {
                alert('Please select an image first');
                return;
            }
            
            const formData = new FormData();
            formData.append('image', file);
            formData.append('return_type', 'base64');
            
            document.getElementById('loading').classList.add('active');
            processBtn.disabled = true;
            
            try {
                const response = await fetch('/remove-bg', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (data.success) {
                    processedImageData = data.image;
                    document.getElementById('processedImage').src = `data:image/png;base64,${data.image}`;
                    document.getElementById('downloadBtn').classList.add('show');
                } else {
                    alert('Error: ' + (data.detail || data.error));
                }
            } catch (error) {
                alert('Error: ' + error.message);
            } finally {
                document.getElementById('loading').classList.remove('active');
                processBtn.disabled = false;
            }
        }
        
        function downloadImage() {
            if (!processedImageData) return;
            
            const link = document.createElement('a');
            link.href = `data:image/png;base64,${processedImageData}`;
            link.download = `bg_removed_${Date.now()}.png`;
            link.click();
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTML_INTERFACE

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Background Remover API"}

@app.post("/remove-bg")
async def remove_background(
    image: UploadFile = File(...),
    return_type: Optional[str] = Form("file"),
    output_format: Optional[str] = Form("png")
):
    # Validate file
    if not validate_file(image.filename):
        raise HTTPException(status_code=400, detail="Invalid file type. Allowed: png, jpg, jpeg, webp")
    
    # Check file size
    contents = await image.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 16MB")
    
    try:
        # Process image
        input_image = Image.open(io.BytesIO(contents))
        
        # Convert RGBA to RGB if necessary for JPEG
        if output_format.lower() == 'jpg' or output_format.lower() == 'jpeg':
            if input_image.mode == 'RGBA':
                # Create a white background
                background = Image.new('RGB', input_image.size, (255, 255, 255))
                background.paste(input_image, mask=input_image.split()[3])
                input_image = background
        
        # Remove background
        output_image = remove(input_image)
        
        if return_type == "base64":
            # Return as base64 JSON
            buffered = io.BytesIO()
            output_image.save(buffered, format=output_format.upper())
            img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            return JSONResponse({
                "success": True,
                "image": img_base64,
                "format": output_format,
                "original_size": list(input_image.size),
                "timestamp": datetime.now().isoformat()
            })
        else:
            # Return as file
            img_io = io.BytesIO()
            output_image.save(img_io, format=output_format.upper())
            img_io.seek(0)
            
            return StreamingResponse(
                img_io,
                media_type=f"image/{output_format}",
                headers={
                    "Content-Disposition": f"attachment; filename=removed_bg_{uuid.uuid4().hex[:8]}.{output_format}"
                }
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/remove-bg-url")
async def remove_background_from_url(image_url: str):
    try:
        import requests
        
        # Download image
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        
        # Process image
        input_image = Image.open(io.BytesIO(response.content))
        output_image = remove(input_image)
        
        # Return as base64
        buffered = io.BytesIO()
        output_image.save(buffered, format='PNG')
        img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        return {
            "success": True,
            "image": img_base64,
            "format": "png",
            "original_size": list(input_image.size),
            "timestamp": datetime.now().isoformat()
        }
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Failed to download image: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
