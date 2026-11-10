# Virtual Hand Drawing

A Python computer vision project that lets you draw flowers and leaves using hand gestures through a webcam.

## Features

- Draw flowers and leaves by raising your index finger
- Pause drawing by raising your index and middle fingers
- Erase around your palm by showing an open palm
- Change flower colors with keys 1–5
- Clear the canvas with C
- Save your drawing as a PNG with S
- Full-screen camera window

## Requirements

- Python 3.14
- A webcam
- Internet connection for installing the required packages

## Setup

### 1. Install the required packages

Open a terminal in the project folder and run:

```bash
python -m pip install opencv-python mediapipe numpy

2. Download the hand tracking model
Download the hand_landmarker.task model and save it in the same folder as main.py.

Your project folder should look like this:
virtual_hand_drawing/
├── main.py
└── hand_landmarker.task
3. Run the project
Open a terminal in the project folder and run:
python main.py
Controls
Control	Action
Raise index finger	Draw flowers and leaves
Raise index and middle fingers	Pause drawing
Show an open palm	Erase around the palm
Press 1–5	Change flower colors
Press C	Clear the canvas
Press S	Save the drawing as a PNG
Press Q	Quit the project


Notes
- Keep hand_landmarker.task in the same folder as main.py.
- Saved drawings appear in the project folder.


    

