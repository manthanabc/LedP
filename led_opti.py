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

def decode_led_signal_live(video_source=0, baud_rate=10, buffer_prefix='000'):
    cap = cv2.VideoCapture(video_source)
    if not cap.isOpened():
        print("Error: Could not open video source.")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0:  # fallback
        fps = 30
    frames_per_bit = fps / baud_rate

    bit_buffer = buffer_prefix
    last_state = 0
    transition_frame = 0
    frame_idx = 0

    print("Receiving data... Press 'q' to stop.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        red_intensity = isolate_red(frame)
        current_state = 1 if red_intensity > 70000 else 0  # threshold can be tuned
        print(f"Frame {frame_idx} | Intensity: {red_intensity:.2f} | State: {current_state}")

        if current_state != last_state:
            duration = frame_idx - transition_frame
            bit_count = int(round(duration / frames_per_bit))
            bit_buffer += str(last_state) * bit_count
            transition_frame = frame_idx

            # Decode and print characters as they are received
            while len(bit_buffer) >= 8:
                byte = bit_buffer[:8]
                bit_buffer = bit_buffer[8:]
                char = chr(int(byte, 2))
                print(char, end='', flush=True)

        last_state = current_state
        frame_idx += 1

        # Exit on pressing 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Handle trailing bits
    if frame_idx > transition_frame:
        duration = frame_idx - transition_frame
        bit_count = int(round(duration / frames_per_bit))
        bit_buffer += str(last_state) * bit_count

    # Final decoding
    while len(bit_buffer) >= 8:
        byte = bit_buffer[:8]
        bit_buffer = bit_buffer[8:]
        print(chr(int(byte, 2)), end='', flush=True)

    cap.release()
    cv2.destroyAllWindows()

# === CHOOSE YOUR INPUT ===
# If you're using USB DroidCam: try 0, 1, 2...
# If you're using WiFi DroidCam: use the HTTP stream URL
# Example: "http://192.168.1.100:4747/video"

# For webcam (DroidCam or real cam):
video_source = 0  # Try 0, 1, or 2 depending on your setup

# For WiFi DroidCam (if applicable), use:
# video_source = "http://192.168.1.100:4747/video"

decode_led_signal_live(video_source, baud_rate=10, buffer_prefix='000')
