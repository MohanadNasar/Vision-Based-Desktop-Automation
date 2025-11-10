# Vision-Based Desktop Automation

A Python tool that finds and clicks desktop icons using computer vision. I built this to automate some repetitive tasks on Windows - it can find the Notepad icon no matter where it's sitting on your desktop.

![Desktop Screenshot](screenshots/desktop.png)
*Screenshot of the desktop with Notepad icon*

## What It Does

The script automatically:
- Finds the Notepad icon on your desktop (even if you moved it)
- Opens Notepad
- Fetches blog posts from an API
- Types each post into Notepad and saves it as a text file

![Icon Detection](screenshots/detection.png)
*The system detecting the Notepad icon*

## Setup

### Install Dependencies

I'm using `uv` for package management, but pip works too:

```bash
uv sync
```

Or with pip:
```bash
pip install -r requirements.txt
```

### Install Tesseract (Optional)

If template matching doesn't work, the script falls back to OCR. You'll need Tesseract for that:

1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
2. Install it (usually goes to `C:\Program Files\Tesseract-OCR`)
3. Make sure it's in your PATH

### Create the Icon Template

Before running, you need a screenshot of your Notepad icon. The first time you run it, it'll guide you through this. Or you can do it manually:

1. Take a screenshot of your desktop
2. Crop just the Notepad icon (with a bit of padding around it)
3. Save it as `assets/notepad_icon.png`

![Icon Template](screenshots/icon_template.png)
*Example of the icon template used for matching*

## Usage

Just run:

```bash
python -m src.main
```

The script will:
1. Take a screenshot of your desktop
2. Find the Notepad icon
3. Double-click it to open Notepad
4. Process 10 posts from the API, typing each one and saving it

![Automation in Action](screenshots/automation.gif)
*The automation running*

## How It Works

It uses template matching to find the icon - basically comparing your desktop screenshot with the icon template. If that doesn't work, it falls back to OCR to find the "Notepad" text and estimates where the icon is.

The multi-scale matching handles different icon sizes (small, medium, large icons in Windows).

## Project Structure

```
├── src/
│   ├── main.py            # Entry point
│   ├── icon_detector.py   # Finds the icon
│   ├── automation.py      # Handles mouse/keyboard
│   └── api_client.py      # Fetches posts
├── assets/
│   └── notepad_icon.png   # Your icon template
└── output/                # Screenshots and results
```

## Notes

- Tested on 1920x1080, might work on other resolutions
- You need a Notepad shortcut on your desktop
- The icon template needs to be captured manually (for now)

## Contact

mohannadnasar99@gmail.com
