# Vision-Based Desktop Automation with Dynamic Icon Grounding

A Python application that uses computer vision to dynamically locate and interact with desktop icons on Windows. The system can find the Notepad icon regardless of its position on the desktop, enabling robust automation even when icon positions change.

## Features

- **Dynamic Icon Detection**: Uses template matching with OCR fallback to locate desktop icons
- **Multi-Scale Matching**: Handles different icon sizes (small, medium, large)
- **Robust Error Handling**: Retry logic, validation, and graceful degradation
- **API Integration**: Fetches blog posts from JSONPlaceholder API
- **Automated Workflow**: Launches Notepad, types content, saves files automatically

## Requirements

- **OS**: Windows 10/11
- **Resolution**: 1920x1080 (tested, may work on other resolutions)
- **Python**: 3.10 or higher
- **Tesseract OCR**: Required for OCR fallback (optional but recommended)

## Installation

### 1. Install Python Dependencies

Using `uv` (recommended):

```bash
uv sync
```

Or using `pip`:

```bash
pip install -r requirements.txt
```

### 2. Install Tesseract OCR (Optional but Recommended)

1. Download Tesseract OCR from: https://github.com/UB-Mannheim/tesseract/wiki
2. Install it (default location: `C:\Program Files\Tesseract-OCR`)
3. Add Tesseract to your PATH, or set the path in your code:
   ```python
   import pytesseract
   pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
   ```

### 3. Create Notepad Shortcut

Before running the application, ensure you have a Notepad shortcut icon on your desktop.

## Usage

### First Run: Capture Icon Template

On the first run, the application will prompt you to capture the Notepad icon template:

1. Run the application:
   ```bash
   python -m src.main
   ```

2. When prompted, follow the instructions to capture the icon:
   - A screenshot will be taken
   - You'll need to crop the Notepad icon region
   - Save it as `notepad_icon.png` in the `assets/` folder

Alternatively, you can manually:
- Take a screenshot of your desktop
- Crop the Notepad icon (include some padding around it)
- Save it as `assets/notepad_icon.png`

### Running the Automation

Once the icon template is set up:

```bash
python -m src.main
```

The application will:
1. Capture a screenshot of the desktop
2. Detect the Notepad icon position
3. Launch Notepad by double-clicking the icon
4. For each of the first 10 posts from the API:
   - Type the post content
   - Save it as `post_{id}.txt` in `Desktop/tjm-project/`
   - Close Notepad
   - Repeat for the next post

### Generating Detection Screenshots

To generate annotated screenshots showing detection in different positions:

```bash
python generate_detection_screenshots.py
```

This will prompt you to move the Notepad icon to:
- Top-left area
- Center of screen
- Bottom-right area

Annotated screenshots will be saved to the `output/` directory.

## Project Structure

```
vision-desktop-automation/
├── pyproject.toml          # uv configuration
├── requirements.txt         # Python dependencies
├── README.md               # This file
├── src/
│   ├── __init__.py
│   ├── main.py            # Main entry point
│   ├── icon_detector.py   # Icon detection (template matching + OCR)
│   ├── automation.py      # Mouse/keyboard automation
│   ├── api_client.py      # JSONPlaceholder API client
│   └── utils.py           # Utility functions
├── assets/
│   └── notepad_icon.png   # Icon template (captured on first run)
├── output/                # Annotated screenshots
└── tests/                 # Test files
```

## How It Works

### Icon Detection Approach

The system uses a **hybrid detection approach**:

1. **Primary Method: Template Matching**
   - Uses OpenCV's template matching algorithm
   - Compares the desktop screenshot with a reference icon template
   - Multi-scale matching handles different icon sizes
   - Fast and accurate when the icon is clearly visible

2. **Fallback Method: OCR Detection**
   - If template matching fails or confidence is too low
   - Uses Tesseract OCR to find "Notepad" text on the desktop
   - Estimates icon position based on text location
   - More flexible but slower and less precise

### Why This Approach?

- **Template Matching**: Fast and reliable for exact visual matches
- **OCR Fallback**: Handles cases where icon appearance changes (themes, sizes)
- **Multi-Scale**: Accommodates different Windows icon size settings
- **Hybrid Design**: Provides robustness without over-engineering

### Failure Cases Handled

- **Icon not found**: Retry up to 3 times with 1-second delays
- **Multiple matching icons**: Selects the one with highest confidence
- **Partially obscured icon**: Lower confidence threshold, tries OCR fallback
- **Different themes**: Grayscale conversion helps normalize appearance
- **Different icon sizes**: Multi-scale template matching
- **API unavailable**: Graceful error message and exit
- **Existing files**: Automatically appends timestamp to filename

## Configuration

Key parameters can be adjusted in the code:

- **Detection confidence threshold**: `TEMPLATE_MATCH_THRESHOLD` in `icon_detector.py` (default: 0.7)
- **Retry attempts**: `MAX_RETRIES` in `icon_detector.py` (default: 3)
- **Retry delay**: `RETRY_DELAY` in `icon_detector.py` (default: 1.0 seconds)
- **Typing speed**: `TYPE_INTERVAL` in `automation.py` (default: 0.05 seconds)

## Troubleshooting

### Icon Not Detected

1. **Check template quality**: Ensure `assets/notepad_icon.png` is clear and recent
2. **Verify icon visibility**: Make sure the Notepad icon is visible on desktop
3. **Try OCR fallback**: Lower the confidence threshold or ensure Tesseract is installed
4. **Check resolution**: Application is optimized for 1920x1080

### Notepad Not Launching

1. **Verify icon detection**: Check logs to see if icon was found
2. **Check window detection**: Ensure Notepad window title is "Notepad"
3. **Manual test**: Try double-clicking the icon manually

### API Connection Issues

1. **Check internet connection**: Ensure you can access JSONPlaceholder API
2. **Firewall**: Check if firewall is blocking requests
3. **Timeout**: API requests have a 10-second timeout

## Performance

- **Icon detection**: Typically 0.5-2 seconds per detection
- **Template matching**: Very fast (< 0.5 seconds)
- **OCR fallback**: Slower (1-3 seconds)
- **Total automation**: ~30-60 seconds for 10 posts (depending on typing speed)

## Limitations

- Optimized for 1920x1080 resolution (may work on others)
- Requires Notepad shortcut on desktop
- Icon template must be captured/created manually
- OCR accuracy depends on desktop text visibility

## Future Improvements

- Support for arbitrary desktop icons (not just Notepad)
- Automatic icon template generation
- Support for different screen resolutions
- Better handling of multiple similar icons
- GUI for configuration and monitoring
- Support for dark/light theme variations

## Discussion Topics

### Icon Detection Approach

**Why template matching over alternatives?**

- **vs. Hardcoded coordinates**: Flexible, works when icon moves
- **vs. Pure OCR**: Faster and more accurate for exact visual matches
- **vs. Machine learning**: Simpler, no training data needed, works out of the box
- **vs. Windows API**: More portable, works across different Windows versions

### Failure Cases

**When would detection fail?**

- Icon completely obscured by windows
- Icon appearance drastically changed (custom icon)
- Very busy desktop background (false positives)
- Icon too small or too large (outside tested scale range)
- Multiple identical icons (may select wrong one)

**How to improve?**

- Use multiple reference templates (different themes/sizes)
- Implement better OCR text-to-icon position estimation
- Add machine learning model for icon classification
- Use Windows API as additional validation
- Implement confidence scoring with multiple methods

### Performance Optimization

**Current performance**: ~0.5-2 seconds per detection

**Optimization strategies:**

- Cache template preprocessing
- Reduce screenshot resolution for initial search
- Use region-of-interest (ROI) if icon location is roughly known
- Parallel processing for multiple icons
- GPU acceleration for template matching

### Robustness

**How does it handle different scenarios?**

- **Different themes**: Grayscale conversion normalizes colors
- **Different icon sizes**: Multi-scale template matching
- **Custom backgrounds**: Confidence threshold filters false positives
- **Multiple similar icons**: Selects highest confidence match
- **Similar names (Notepad vs. Notepad++)**: Template matching distinguishes visually

### Scaling

**How to extend to any arbitrary icon?**

1. Generalize template capture (user selects any icon)
2. Support multiple icon templates simultaneously
3. Add icon name/description for identification
4. Implement icon database with metadata

**How to work on different resolutions?**

1. Scale template based on screen resolution
2. Use relative coordinates instead of absolute
3. Test and calibrate for common resolutions
4. Add resolution detection and auto-scaling

### Alternative Approaches

**What would you do differently with more time?**

1. **Machine Learning**: Train a CNN to detect icons generically
2. **Windows API Integration**: Use Windows accessibility APIs for more reliable detection
3. **Hybrid Approach**: Combine vision with Windows API for validation
4. **Icon Database**: Build a database of common Windows icons
5. **GUI Application**: Create a user-friendly interface for configuration
6. **Cross-Platform**: Extend to Linux/Mac using platform-specific APIs

## License

This project is provided as-is for educational and demonstration purposes.

## Author

mohannadnasar99@gmail.com
