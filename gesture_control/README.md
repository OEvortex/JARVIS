# Gesture Control System

A Python-based gesture control system that allows you to control your computer mouse using hand gestures.

## Features

- Real-time hand tracking
- Mouse movement control
- Gesture recognition for:
  - Left click
  - Right click
  - Scrolling
  - Cursor movement

## Requirements

- Python 3.7+
- OpenCV
- Mediapipe
- PyAutoGUI
- NumPy

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the main script:
```bash
python main.py
```

### Gestures

- Index finger up: Left click
- Quick double index finger: Double click
- Index + Middle fingers up: Right click
- All fingers up: Move cursor
- Index + Middle + Ring fingers up: Scroll
- Thumb + Index finger: Drag and drop
- All fingers up (palm up/down): Volume control
- Three fingers up (palm up/down): Brightness control
- All fingers spread with palm facing camera: Take screenshot

## Advanced Features

- Gesture History Tracking
- Smart Double-Click Detection
- Drag and Drop Support
- System Control:
  - Volume adjustment
  - Screen brightness
  - Screenshot capture

## Configuration

Adjust settings in `config/settings.py` to customize:
- Camera settings
- Hand detection parameters
- Mouse control sensitivity
