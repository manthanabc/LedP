import cv2
import numpy as np

def isolate_red(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    lower_red1 = np.array([0, 120, 70])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 120, 70])
    upper_red2 = np.array([180, 255, 255])

    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)

    red_mask = mask1 + mask2

    return np.sum(red_mask) / 255

def decode_led_signal_streaming(video_source, baud_rate=10):
    cap = cv2.VideoCapture(video_source)
    if not cap.isOpened():
        print("Error: Could not open video source.")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0 or fps is None:
        fps = 30  # fallback default
    frames_per_bit = fps / baud_rate

    bit_buffer = "000"
    last_state = 0
    transition_frame = 0
    frame_idx = 0

    print("Receiving data... Press 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        red_intensity = isolate_red(frame)
        current_state = 1 if red_intensity > 80000 else 0
        # print(red_intensity)

        if current_state != last_state:
            duration = frame_idx - transition_frame
            bit_count = int(round(duration / frames_per_bit))
            bit_buffer += str(last_state) * bit_count

            # Apply 3-bit left shift
            while len(bit_buffer) >= 8:
                byte = bit_buffer[:8]
                bit_buffer = bit_buffer[8:]
                char = chr(int(byte, 2))
                print(char, end='', flush=True)

            transition_frame = frame_idx

        last_state = current_state
        frame_idx += 1

        # Exit if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Final leftover processing
    if frame_idx > transition_frame:
        duration = frame_idx - transition_frame
        bit_count = int(round(duration / frames_per_bit))
        bit_buffer += str(last_state) * bit_count

    while len(bit_buffer) >= 8:
        byte = bit_buffer[:8]
        bit_buffer = bit_buffer[8:]
        print(chr(int(byte, 2)), end='', flush=True)

    cap.release()
    cv2.destroyAllWindows()

# --- Choose your video source here ---
# For USB DroidCam or webcam
video_source = 1  # try 0, 1, 2

# OR for WiFi DroidCam, use the IP shown in DroidCam app:
# video_source = "http://192.168.1.100:4747/video"

decode_led_signal_streaming(video_source)
