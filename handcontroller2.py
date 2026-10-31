import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import time
import math
from collections import deque

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    model_complexity=0,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7,
)
mp_draw = mp.solutions.drawing_utils

screen_w, screen_h = pyautogui.size()

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 60)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

prev_x, prev_y = 0, 0
smooth_factor = 4.0
frame_margin = 90

last_action_time = 0
last_scroll_time = 0
one_finger_start_time = None
clicked_this_hold = False

palm_history = deque(maxlen=6)
gesture_buffer = deque(maxlen=4)


def fingers_up(landmarks):
    fingers = []
    # Check 4 fingers [Index, Middle, Ring, Pinky] with strict margin to stop flickering
    for tip_id in [8, 12, 16, 20]:
        if landmarks[tip_id].y < landmarks[tip_id - 2].y - 0.02:
            fingers.append(1)
        else:
            fingers.append(0)
    return fingers


while cap.isOpened():
    success, img = cap.read()
    if not success:
        break

    img = cv2.flip(img, 1)
    h, w, _ = img.shape

    cv2.rectangle(
        img,
        (frame_margin, frame_margin - 20),
        (w - frame_margin, h - frame_margin - 20),
        (255, 0, 255),
        2,
    )

    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_img)

    current_time = time.time()
    gesture_text = "Idle"

    if results.multi_hand_landmarks:
        hand_landmarks = results.multi_hand_landmarks[0]
        mp_draw.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)
        lm = hand_landmarks.landmark

        four_fingers = fingers_up(lm)
        gesture_buffer.append(four_fingers)

        # Confirm gesture only if it stays stable for 4 frames (Stops screen shaking)
        stable_gesture = (
            four_fingers
            if gesture_buffer.count(four_fingers) == len(gesture_buffer)
            else None
        )

        palm_x, palm_y = int(lm[9].x * w), int(lm[9].y * h)

        # 1. FIVE FINGERS -> Move Mouse & Fast Swipe Left/Right
        if stable_gesture == [1, 1, 1, 1]:
            one_finger_start_time = None
            clicked_this_hold = False
            palm_history.append((palm_x, current_time))

            swiped = False
            if len(palm_history) >= 5 and (current_time - last_action_time > 0.6):
                dx = palm_history[-1][0] - palm_history[0][0]
                dt = palm_history[-1][1] - palm_history[0][1]

                if 0 < dt < 0.25 and abs(dx) > 130:
                    if dx > 0:
                        gesture_text = "Swipe Right ->"
                        pyautogui.press("right")
                    else:
                        gesture_text = "<- Swipe Left"
                        pyautogui.press("left")
                    last_action_time = current_time
                    palm_history.clear()
                    swiped = True

            if not swiped and (current_time - last_action_time > 0.3):
                gesture_text = "5 Fingers: Moving Mouse"
                cv2.circle(img, (palm_x, palm_y), 10, (255, 0, 255), cv2.FILLED)

                raw_x = np.interp(palm_x, [frame_margin, w - frame_margin], [0, screen_w])
                raw_y = np.interp(
                    palm_y, [frame_margin - 20, h - frame_margin - 20], [0, screen_h]
                )

                curr_x = prev_x + (raw_x - prev_x) / smooth_factor
                curr_y = prev_y + (raw_y - prev_y) / smooth_factor

                if math.hypot(curr_x - prev_x, curr_y - prev_y) > 2.5:
                    pyautogui.moveTo(curr_x, curr_y, _pause=False)
                    prev_x, prev_y = curr_x, curr_y

        # 2. ONE FINGER (Index Only) -> Hold to Click / Open App
        elif stable_gesture == [1, 0, 0, 0]:
            palm_history.clear()
            ix, iy = int(lm[8].x * w), int(lm[8].y * h)

            if one_finger_start_time is None:
                one_finger_start_time = current_time
                clicked_this_hold = False

            hold_duration = current_time - one_finger_start_time

            if not clicked_this_hold:
                progress = min(hold_duration / 0.6, 1.0)
                cv2.ellipse(
                    img,
                    (ix, iy),
                    (20, 20),
                    0,
                    0,
                    int(360 * progress),
                    (0, 255, 0),
                    4,
                )
                gesture_text = f"Clicking... {int(progress * 100)}%"

                if hold_duration >= 0.6:
                    pyautogui.doubleClick()
                    gesture_text = "Clicked / Opened!"
                    clicked_this_hold = True
                    last_action_time = current_time
            else:
                gesture_text = "Clicked!"

        # 3. TWO FINGERS (Index + Middle) -> Smooth Scroll Down (Home Feed + Reels)
        elif stable_gesture == [1, 1, 0, 0]:
            palm_history.clear()
            one_finger_start_time = None
            clicked_this_hold = False
            gesture_text = "2 Fingers: Scrolling Down"

            if current_time - last_scroll_time > 0.08:
                pyautogui.scroll(-120)
                last_scroll_time = current_time

        # 4. THREE FINGERS (Index + Middle + Ring) -> Smooth Scroll Up (Home Feed + Reels)
        elif stable_gesture == [1, 1, 1, 0]:
            palm_history.clear()
            one_finger_start_time = None
            clicked_this_hold = False
            gesture_text = "3 Fingers: Scrolling Up"

            if current_time - last_scroll_time > 0.08:
                pyautogui.scroll(120)
                last_scroll_time = current_time

        else:
            palm_history.clear()
            one_finger_start_time = None
    else:
        palm_history.clear()
        gesture_buffer.clear()
        one_finger_start_time = None
        clicked_this_hold = False

    cv2.putText(
        img, gesture_text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2
    )

    cv2.imshow("Stable Gesture Controller", img)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()