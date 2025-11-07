# Installation Guide

## Quick Start

### Option 1: Using pip (Recommended for Python 3.9+)

```bash
python -m pip install -r requirements.txt
```

### Option 2: Using uv

If you have `uv` installed:

```bash
uv sync
```

## Dependencies Installed

✅ **Python Packages** (automatically installed):
- `pyautogui` - Mouse and keyboard automation
- `opencv-python` - Image processing and template matching
- `pytesseract` - OCR wrapper (requires Tesseract OCR below)
- `pillow` - Image manipulation
- `requests` - HTTP requests for API
- `numpy` - Numerical operations

## Optional: Tesseract OCR Installation

The OCR fallback feature requires Tesseract OCR to be installed separately:

### Windows Installation:

1. **Download Tesseract:**
   - Visit: https://github.com/UB-Mannheim/tesseract/wiki
   - Download the Windows installer (e.g., `tesseract-ocr-w64-setup-5.x.x.exe`)

2. **Install:**
   - Run the installer
   - **Important:** Note the installation path (usually `C:\Program Files\Tesseract-OCR`)

3. **Add to PATH (Optional but Recommended):**
   - Add `C:\Program Files\Tesseract-OCR` to your system PATH
   - Or set it in code (see below)

4. **Verify Installation:**
   ```bash
   tesseract --version
   ```

### If Tesseract is not in PATH:

If Tesseract is installed but not in PATH, you can set it in your code:

```python
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

**Note:** The application will work without Tesseract, but the OCR fallback will be unavailable. Template matching will still work as the primary detection method.

## Verification

Test that everything is installed:

```bash
python -c "import pyautogui, cv2, pytesseract, PIL, requests, numpy; print('All packages OK!')"
```

## Troubleshooting

### Import Errors

If you get import errors:
1. Make sure you're using the correct Python version (3.9+)
2. Try: `python -m pip install --upgrade pip`
3. Reinstall: `python -m pip install -r requirements.txt --force-reinstall`

### Tesseract Not Found

- The application will work without Tesseract
- Only the OCR fallback feature will be unavailable
- Template matching (primary method) will still work

### OpenCV Issues

If OpenCV installation fails:
- Try: `python -m pip install opencv-python-headless` (lighter version)
- Or: `python -m pip install opencv-contrib-python` (full version)





