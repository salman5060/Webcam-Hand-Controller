# Webcam-Hand-Controller
A Python script that lets you control your mouse, click, scroll, and swipe using hand gestures via your webcam. Built with OpenCV, MediaPipe, and PyAutoGUI.
Controls & Gestures
Keep your hand inside the purple frame on the camera window for accurate tracking:
 * Move Cursor: Show all 5 fingers (open palm) and move your hand around.
 * Left/Right Swipe: Flicker your palm quickly to the left or right to press arrow keys.
 * Click / Open: Hold up 1 finger (index) for 0.6 seconds until the green circle completes to trigger a double-click.
 * Scroll Down: Hold up 2 fingers (index + middle).
 * Scroll Up: Hold up 3 fingers (index + middle + ring).
 * Exit: Press ESC while the camera window is active.
Setup & Usage
Installa required libraries:
pip install opencv-python mediapipe numpy pyautogui
Run the script:
python main.py
