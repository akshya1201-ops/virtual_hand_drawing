import cv2
import mediapipe as mp
import numpy as np
import ctypes
import math
import random
from datetime import datetime
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

MODEL_PATH = "hand_landmarker.task"

# MediaPipe hand detector setup
base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.VIDEO,
    num_hands=1,
    min_hand_detection_confidence=0.5,
    min_tracking_confidence=0.5
)
detector = vision.HandLandmarker.create_from_options(options)

# Flower colors (BGR format)
palettes = {
    "1": ("Rose",   [(40, 70, 220), (80, 100, 245), (30, 45, 180)]),
    "2": ("Sunset", [(20, 120, 230), (40, 170, 245), (30, 80, 190)]),
    "3": ("Violet", [(170, 70, 180), (210, 100, 220), (120, 45, 150)]),
    "4": ("Garden", [(40, 150, 60), (60, 190, 90), (25, 110, 40)]),
    "5": ("Ocean",  [(180, 100, 30), (220, 150, 50), (130, 70, 20)]),
}
current_palette_name, current_palette = palettes["1"]

camera = cv2.VideoCapture(0)

# Canvas and drawing state
canvas = None
previous_point = None
distance_since_flower = 0
timestamp_ms = 0
window_name = "Virtual Flower Drawing"


def draw_flower(image, x, y, angle, palette):
    """Draw one defined flower with outlined petals and veined leaves."""
    outline = (20, 20, 20)
    petal_radius = 7
    petal_distance = 8

    # Seven petals
    for i in range(7):
        a = angle + (2 * math.pi * i / 7)
        px = int(x + math.cos(a) * petal_distance)
        py = int(y + math.sin(a) * petal_distance)

        color = palette[i % len(palette)]

        # Dark outline and colored petal
        cv2.circle(image, (px, py), petal_radius + 1, outline, -1, cv2.LINE_AA)
        cv2.circle(image, (px, py), petal_radius, color, -1, cv2.LINE_AA)

        # Petal highlight
        highlight = tuple(min(255, c + 35) for c in color)
        hx = int(px - math.cos(a) * 2)
        hy = int(py - math.sin(a) * 2)
        cv2.circle(image, (hx, hy), 2, highlight, -1, cv2.LINE_AA)

    # Yellow flower center
    cv2.circle(image, (x, y), 5, outline, -1, cv2.LINE_AA)
    cv2.circle(image, (x, y), 4, (20, 220, 255), -1, cv2.LINE_AA)

    # Two green leaves with dark outlines and veins
    for side in (-1, 1):
        leaf_angle = angle + side * 1.1
        lx = int(x + math.cos(leaf_angle) * 15)
        ly = int(y + math.sin(leaf_angle) * 15)

        cv2.ellipse(
            image, (lx, ly), (4, 9),
            math.degrees(leaf_angle), 0, 360,
            outline, -1, cv2.LINE_AA
        )
        cv2.ellipse(
            image, (lx, ly), (3, 8),
            math.degrees(leaf_angle), 0, 360,
            (35, 160, 45), -1, cv2.LINE_AA
        )

        # Leaf vein
        cv2.line(image, (x, y), (lx, ly), (170, 210, 120), 1, cv2.LINE_AA)


def finger_is_up(tip, joint):
    return tip.y < joint.y


def is_open_palm(hand):
    """Check whether all four fingers and the thumb are extended."""
    four_fingers_up = (
        finger_is_up(hand[8], hand[6]) and
        finger_is_up(hand[12], hand[10]) and
        finger_is_up(hand[16], hand[14]) and
        finger_is_up(hand[20], hand[18])
    )

    # Thumb extended away from the palm
    thumb_extended = abs(hand[4].x - hand[5].x) > abs(hand[3].x - hand[5].x)

    return four_fingers_up and thumb_extended


# Full-screen camera window
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
cv2.setWindowProperty(
    window_name,
    cv2.WND_PROP_FULLSCREEN,
    cv2.WINDOW_FULLSCREEN
)

while True:
    success, frame = camera.read()

    if not success:
        print("Camera open aagala. Camera connection check pannunga.")
        break

    frame = cv2.flip(frame, 1)
    height, width, _ = frame.shape

    if canvas is None:
        canvas = np.zeros_like(frame)

    # Detect hand
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb_frame
    )

    timestamp_ms += 33
    result = detector.detect_for_video(mp_image, timestamp_ms)

    mode_text = "Index finger: draw"
    cursor_point = None

    if result.hand_landmarks:
        hand = result.hand_landmarks[0]

        # Palm center for erasing
        palm_ids = [0, 5, 9, 13, 17]
        palm_x = int(sum(hand[i].x for i in palm_ids) / len(palm_ids) * width)
        palm_y = int(sum(hand[i].y for i in palm_ids) / len(palm_ids) * height)

        index_up = finger_is_up(hand[8], hand[6])
        middle_up = finger_is_up(hand[12], hand[10])
        palm_open = is_open_palm(hand)

        if palm_open:
            # Open palm erases around the palm
            cv2.circle(canvas, (palm_x, palm_y), 75, (0, 0, 0), -1)
            cv2.circle(frame, (palm_x, palm_y), 75, (255, 255, 255), 2)
            mode_text = "Open palm: erase"
            previous_point = None
            distance_since_flower = 0

        elif index_up and middle_up:
            # Two fingers pause drawing
            mode_text = "Two fingers: paused"
            previous_point = None
            distance_since_flower = 0

        elif index_up and not middle_up:
            # Index fingertip draws the flowers
            x = int(hand[8].x * width)
            y = int(hand[8].y * height)
            cursor_point = (x, y)
            mode_text = f"Drawing: {current_palette_name}"

            if previous_point is None:
                draw_flower(
                    canvas, x, y,
                    random.random() * 2 * math.pi,
                    current_palette
                )
                distance_since_flower = 0
            else:
                old_x, old_y = previous_point
                dx = x - old_x
                dy = y - old_y
                distance = math.hypot(dx, dy)

                if distance > 0:
                    angle = math.atan2(dy, dx)
                    distance_since_flower += distance

                    while distance_since_flower >= 32:
                        draw_flower(
                            canvas, x, y,
                            angle + random.uniform(-0.5, 0.5),
                            current_palette
                        )
                        distance_since_flower -= 32

            previous_point = (x, y)

        else:
            previous_point = None
            distance_since_flower = 0

    else:
        previous_point = None
        distance_since_flower = 0

    # Put drawing on camera image at full opacity
    output = frame.copy()
    drawing_mask = np.any(canvas != 0, axis=2)
    output[drawing_mask] = canvas[drawing_mask]

    # On-screen controls
    cv2.rectangle(output, (10, 10), (500, 105), (25, 25, 25), -1)
    cv2.putText(
        output, mode_text, (20, 38),
        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2
    )
    cv2.putText(
        output, "1-5: Flower colors | C: Clear | S: Save",
        (20, 66), cv2.FONT_HERSHEY_SIMPLEX, 0.48,
        (255, 255, 255), 1
    )
    cv2.putText(
        output, "Q: Quit | Index: draw | Two fingers: pause",
        (20, 91), cv2.FONT_HERSHEY_SIMPLEX, 0.45,
        (255, 255, 255), 1
    )

    if cursor_point is not None:
        cv2.circle(output, cursor_point, 7, (255, 255, 255), 2)

    cv2.imshow(window_name, output)

    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break

    elif key in [ord(k) for k in palettes]:
        current_palette_name, current_palette = palettes[chr(key)]

    elif key == ord("c"):
        canvas[:] = 0
        previous_point = None
        distance_since_flower = 0

    elif key == ord("s"):
        # Save drawing on a white background
        saved_image = np.full_like(canvas, 255)
        mask = np.any(canvas != 0, axis=2)
        saved_image[mask] = canvas[mask]

        filename = "flower_drawing_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".png"
        cv2.imwrite(filename, saved_image)
        print(f"Drawing saved: {filename}")

camera.release()
detector.close()
cv2.destroyAllWindows()