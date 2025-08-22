# Background Remover API 🎨

Fast, simple background removal for images using FastAPI + rembg (ONNX). Upload an image or pass a URL, and get a clean cutout with transparent background. Comes with a minimal, responsive web UI and OpenAPI docs.

- Live docs: `/docs`
- Web UI: `/`
- Health check: `/health`

## Features

- Upload or URL-based background removal
- PNG, JPG, JPEG, WEBP input support
- PNG output by default (transparent)
- Base64 or file streaming response
- CORS enabled (allow all) for easy integration
- Handy built-in HTML playground

## Stack

- FastAPI + Uvicorn
- rembg + onnxruntime (U^2-Net under the hood)
- Pillow for image handling

## Project structure

```
sugamdeol-remove-bg-api/
├── app.py
├── render.yaml
├── requirements.txt
└── runtime.txt
```

## Quick start (local)

Requirements:
- Python 3.10+ (tested with 3.10/3.11)
- pip

Steps:
```bash
# 1) Clone
git clone <this-repo-url>
cd sugamdeol-remove-bg-api

# 2) Create venv
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows
.venv\Scripts\activate

# 3) Install deps
pip install -r requirements.txt

# 4) Run
python app.py
# or with reload:
# uvicorn app:app --host 0.0.0.0 --port 10000 --reload
```

Open:
- Web UI: http://localhost:10000/
- Docs: http://localhost:10000/docs

Note: On the first request, rembg downloads the model; the first call may take longer.

## API Endpoints

| Method | Path            | Description                                | Notes |
|-------:|------------------|--------------------------------------------|-------|
| GET    | `/`              | Minimal HTML UI                            | Upload → preview → download |
| GET    | `/health`        | Health check                               | Returns JSON |
| POST   | `/remove-bg`     | Remove background from uploaded image      | multipart/form-data |
| POST   | `/remove-bg-url` | Remove background from image URL           | Pass image_url as query param |
| GET    | `/docs`          | Swagger UI                                 | Interactive API |
| GET    | `/redoc`         | ReDoc                                      | Alternative docs |

### 1) Upload an image

Request (multipart/form-data):
- image: file (required) [png, jpg, jpeg, webp]
- return_type: string (optional) "base64" or "file" (default: "file")
- output_format: string (optional) "png", "jpg", or "jpeg" (default: "png")

Example (return a file stream as response):
```bash
curl -X POST http://localhost:10000/remove-bg \
  -F "image=@/path/to/photo.jpg"
```

Example (JSON with base64):
```bash
curl -X POST http://localhost:10000/remove-bg \
  -F "image=@/path/to/photo.jpg" \
  -F "return_type=base64" \
  -F "output_format=png"
```

Sample JSON response:
```json
{
  "success": true,
  "image": "iVBORw0KGgoAAAANSUhEUgAA...", 
  "format": "png",
  "original_size": [1024, 768],
  "timestamp": "2025-01-01T12:34:56.789012"
}
```

JavaScript example:
```js
const form = new FormData();
form.append('image', fileInput.files[0]);
form.append('return_type', 'base64'); // or 'file'
form.append('output_format', 'png');

const res = await fetch('/remove-bg', { method: 'POST', body: form });
const data = await res.json();
const imgSrc = `data:image/${data.format};base64,${data.image}`;
```

### 2) Remove background from a URL

- Method: POST
- Parameter: image_url (query param)

Example:
```bash
curl -X POST "http://localhost:10000/remove-bg-url?image_url=https://example.com/cat.jpg"
```

Response: JSON with base64 PNG.

## Web UI

A simple, responsive UI is embedded at `/`:
- Drag & drop or pick an image
- Preview original and processed result
- Download processed PNG

## Constraints and behavior

- Allowed inputs: PNG, JPG, JPEG, WEBP
- Max file size: 16 MB (server returns 413 if exceeded)
- Default output: PNG (recommended)
- CORS: allowed for all origins

Important notes about JPEG:
- Transparency is not supported by JPEG. For best results, keep output_format=png.
- If you force output_format=jpg/jpeg and encounter “cannot write mode RGBA as JPEG”, switch to PNG. Transparent cutouts require PNG.

## Deploy on Render

This repo includes render.yaml for one-click deployment.

Steps:
1. Push the repo to GitHub/GitLab.
2. In Render, “New +” → “Blueprint” → select your repo.
3. Render will read render.yaml and create a Web Service.
4. First build may take longer due to dependency/model downloads.

Notes:
- render.yaml sets PYTHON_VERSION=3.10.13. runtime.txt lists python-3.11.9. Align these if you prefer a single version; Render will honor the env var.

## Configuration

- PORT: The app reads PORT from the environment (default 10000).
- CORS: Currently allow-all. Consider restricting in production.

## Troubleshooting

- 400 Invalid file type: Only png, jpg, jpeg, webp are accepted.
- 413 File too large: Compress or resize your image under 16MB.
- 500 cannot write mode RGBA as JPEG: Use output_format=png (JPEG has no transparency).
- 400 Failed to download image: Ensure the URL is public and reachable; try again or increase timeout if needed.
- Cold start slow: First request downloads ONNX model for rembg; subsequent requests are faster.

## Acknowledgments

- rembg: https://github.com/danielgatis/rembg
- FastAPI: https://fastapi.tiangolo.com/
- onnxruntime: https://onnxruntime.ai/

Happy cutting! ✂️🖼️
