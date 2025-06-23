import cv2
import numpy as np
from tkinter import filedialog, Tk, Button, Label, Text, END
from PIL import Image, ImageTk
import threading

# ---------------------------------------
# Hamming(12,8) Decoder and Red Isolator
# ---------------------------------------

def isolate_red(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower_red1 = np.array([0, 120, 70])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 120, 70])
    upper_red2 = np.array([180, 255, 255])
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    red_mask = mask1 + mask2
    return red_mask

def hamming_decode_12bit(codeword):
    bits = [(codeword >> i) & 1 for i in range(11, -1, -1)]
    p1, p2, d1, p3, d2, d3, d4, p4, d5, d6, d7, d8 = bits

    s1 = p1 ^ d1 ^ d2 ^ d4 ^ d5 ^ d7
    s2 = p2 ^ d1 ^ d3 ^ d4 ^ d6 ^ d7
    s3 = p3 ^ d2 ^ d3 ^ d4 ^ d8
    s4 = p4 ^ d5 ^ d6 ^ d7 ^ d8

    error_pos = (s1 << 3) | (s2 << 2) | (s3 << 1) | s4
    had_error = (error_pos != 0)

    if 1 <= error_pos <= 12:
        bits[error_pos - 1] ^= 1

    data_bits = [bits[2], bits[4], bits[5], bits[6], bits[8], bits[9], bits[10], bits[11]]
    byte = 0
    for b in data_bits:
        byte = (byte << 1) | b

    return chr(byte), had_error

def process_frames_segment(frames, fps, baud_rate=10, alpha=0.05):
    frames_per_bit = fps / baud_rate
    bit_stream = "000"
    last_state = 0
    transition_frame = 0
    threshold = None

    for frame_idx, frame in enumerate(frames):
        red_intensity = np.sum(isolate_red(frame)) / 255
        threshold = red_intensity if threshold is None else alpha * red_intensity + (1 - alpha) * threshold
        current_state = 1 if red_intensity > threshold else 0

        if current_state != last_state:
            duration = frame_idx - transition_frame
            bit_count = int(round(duration / frames_per_bit))
            bit_stream += str(last_state) * bit_count
            transition_frame = frame_idx

        last_state = current_state

    duration = len(frames) - transition_frame
    bit_count = int(round(duration / frames_per_bit))
    bit_stream += str(last_state) * bit_count

    best_output = ""
    max_clean_chars = 0

    for shift in range(12):
        shifted_bits = bit_stream[shift:]
        output = ''
        clean_count = 0

        while len(shifted_bits) >= 12:
            codeword = shifted_bits[:12]
            shifted_bits = shifted_bits[12:]
            try:
                char, had_error = hamming_decode_12bit(int(codeword, 2))
                if not had_error:
                    output += char
                    clean_count += 1
            except Exception:
                continue

        if clean_count > max_clean_chars:
            max_clean_chars = clean_count
            best_output = output

    return best_output

def decode_led_signal_chunked(cap, display_callback, text_callback, baud_rate=10, chunk_duration=10):
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0 or np.isnan(fps):
        fps = 30

    chunk_size = int(fps * chunk_duration)
    frames = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frames.append(frame)

        # Show preview
        display_callback(frame)

        if len(frames) == chunk_size:
            output = process_frames_segment(frames, fps, baud_rate)
            text_callback(output)
            frames = []

    if frames:
        output = process_frames_segment(frames, fps, baud_rate)
        text_callback(output)

    cap.release()


# -------------------------------
# GUI
# -------------------------------

class LEDDecoderGUI:
    def __init__(self, master):
        self.master = master
        master.title("LED Signal Decoder")

        self.video_path = None
        self.video_source = None
        self.cap = None

        self.select_button = Button(master, text="📁 Select Video File", command=self.select_file)
        self.select_button.pack()

        self.webcam_button = Button(master, text="🎥 Use Webcam", command=self.use_webcam)
        self.webcam_button.pack()

        self.video_label = Label(master)
        self.video_label.pack()

        self.mask_label = Label(master)
        self.mask_label.pack()

        self.output_text = Text(master, height=5, width=50)
        self.output_text.pack()

        self.decode_button = Button(master, text="▶️ Start Decoding", command=self.start_decoding)
        self.decode_button.pack()

    def select_file(self):
        self.video_path = filedialog.askopenfilename(filetypes=[("MP4 files", "*.mp4")])
        if self.video_path:
            self.cap = cv2.VideoCapture(self.video_path)
            ret, frame = self.cap.read()
            if ret:
                self.display_frame(frame)
            self.cap.release()

    def use_webcam(self):
        self.cap = cv2.VideoCapture(0)
        ret, frame = self.cap.read()
        if ret:
            self.display_frame(frame)
        self.cap.release()

    def display_frame(self, frame):
        frame = cv2.resize(frame, (320, 240))
        red_mask = isolate_red(frame)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb)
        img_tk = ImageTk.PhotoImage(image=img)
        self.video_label.configure(image=img_tk)
        self.video_label.image = img_tk

        mask_rgb = cv2.cvtColor(red_mask, cv2.COLOR_GRAY2RGB)
        mask_img = Image.fromarray(mask_rgb)
        mask_img_tk = ImageTk.PhotoImage(image=mask_img)
        self.mask_label.configure(image=mask_img_tk)
        self.mask_label.image = mask_img_tk

    def update_text(self, txt):
        self.output_text.insert(END, txt + '\n')
        self.output_text.see(END)

    def start_decoding(self):
        if self.video_path:
            self.cap = cv2.VideoCapture(self.video_path)
        else:
            self.cap = cv2.VideoCapture(0)

        if not self.cap.isOpened():
            self.update_text("Error: Could not open video source.")
            return

        t = threading.Thread(target=decode_led_signal_chunked, args=(
            self.cap,
            self.display_frame,
            self.update_text,
        ))
        t.start()


# -------------------------------
# Run the app
# -------------------------------

if __name__ == "__main__":
    root = Tk()
    app = LEDDecoderGUI(root)
    root.mainloop()
