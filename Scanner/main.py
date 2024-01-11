import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import cv2
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r'Tesseract-OCR\tesseract.exe'

allowed_plate_numbers = ['H283TX 37', 'H283TX37', 'QWE456']


def check_plate_number(plate_number):
    if plate_number.strip() in allowed_plate_numbers:
        return "Допущен"
    else:
        return "Запрещен"


def carplate_extract(image, carplate_haar_cascade):
    carplate_rects = carplate_haar_cascade.detectMultiScale(image, scaleFactor=1.1, minNeighbors=5)
    for x, y, w, h in carplate_rects:
        carplate_img = image[y + 15:y + h - 10, x + 15:x + w - 20]
    return carplate_img


def enlarge_img(image, scale_percent):
    width = int(image.shape[1] * scale_percent / 100)
    height = int(image.shape[0] * scale_percent / 100)
    dim = (width, height)
    resized_image = cv2.resize(image, dim, interpolation=cv2.INTER_AREA)
    return resized_image


class CarPlateApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.geometry("1920x1080")
        self.title("Распознавание номеров авто")

        self.history = []
        self.max_history_entries = 7

        main_frame = ttk.Frame(self)
        main_frame.pack(side="left", padx=10, pady=10)

        image_frame = ttk.Frame(main_frame)
        image_frame.pack(side="top", anchor="nw")

        self.image_label = ttk.Label(image_frame)
        self.image_label.pack(padx=10, pady=10)

        vertical_line1 = ttk.Frame(self, width=2, style="TSeparator")
        vertical_line1.pack(side="left", fill="y", padx=5, pady=10)
        style = ttk.Style()
        style.configure("TSeparator", background="black")

        self.last_plate_label = ttk.Label(self, text="Последний номер: ", font=("Arial", 20))
        self.last_plate_label.pack(padx=10, pady=10)

        self.last_plate_image_labels = []
        for _ in range(self.max_history_entries):
            label = ttk.Label(self)
            label.pack(side="top", padx=10, pady=5)
            self.last_plate_image_labels.append(label)


        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side="bottom", anchor="w", pady=10)

        style = ttk.Style()
        style.configure("TButton", padding=(150, 30))

        self.start_button = ttk.Button(button_frame, text="Старт", command=self.start_camera, style="TButton")
        self.start_button.pack(side='left', padx=0, pady=10)

        self.stop_button = ttk.Button(button_frame, text="Стоп", command=self.stop_camera, style="TButton")
        self.stop_button.pack(side='left', padx=0, pady=10)

        self.cap = None
        self.carplate_haar_cascade = cv2.CascadeClassifier(
            'haar_cascades/haarcascade_russian_plate_number.xml')

        self.start_camera()


    def start_camera(self):
        if self.cap is None:
            self.cap = cv2.VideoCapture(0)
        self.update_frame()

    def add_to_history(self, carplate_text, carplate_image):
        entry = {"carplate_text": carplate_text, "carplate_image": carplate_image}
        self.history.append(entry)
        if len(self.history) > self.max_history_entries:
            del self.history[0]

        for idx, hist_entry in enumerate(self.history[-self.max_history_entries:]):
            carplate_text = hist_entry["carplate_text"]
            last_plate_image = hist_entry["carplate_image"]

            last_plate_image_with_text = last_plate_image.copy()
            cv2.putText(last_plate_image_with_text, carplate_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            last_plate_image_with_text = Image.fromarray(cv2.cvtColor(last_plate_image_with_text, cv2.COLOR_BGR2RGB))
            last_plate_image_with_text = last_plate_image_with_text.resize((200, 100), Image.BICUBIC)
            last_plate_image_tk = ImageTk.PhotoImage(image=last_plate_image_with_text)

            label_text = f"Номер машины: {carplate_text}\nСтатус допуска: {check_plate_number(carplate_text)}"
            self.last_plate_image_labels[idx].configure(image=last_plate_image_tk, text=label_text, compound='left', font=("Arial", 15))
            self.last_plate_image_labels[idx].image = last_plate_image_tk

        last_plate_image = Image.fromarray(cv2.cvtColor(carplate_image, cv2.COLOR_BGR2RGB))
        last_plate_image = last_plate_image.resize((730, 450), Image.BICUBIC)
        last_plate_image_tk = ImageTk.PhotoImage(image=last_plate_image)
        self.image_label.imgtk = last_plate_image_tk
        self.image_label.configure(image=last_plate_image_tk)

    def update_frame(self):
        if self.cap is not None and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                try:
                    carplate_extract_img = carplate_extract(frame_rgb, self.carplate_haar_cascade)
                    carplate_extract_img = enlarge_img(carplate_extract_img, 300)

                    carplate_extract_img_gray = cv2.cvtColor(carplate_extract_img, cv2.COLOR_RGB2GRAY)

                    carplate_text = pytesseract.image_to_string(
                        carplate_extract_img_gray,
                        config='--psm 6 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789').strip()

                    self.add_to_history(carplate_text, carplate_extract_img)

                except Exception as e:
                    print("Error:", e)

                pil_image = Image.fromarray(frame_rgb)
                pil_image = pil_image.resize((730, 450), Image.BICUBIC)
                imgtk = ImageTk.PhotoImage(image=pil_image)
                self.image_label.imgtk = imgtk
                self.image_label.configure(image=imgtk)

            self.after(3000, self.update_frame)

    def stop_camera(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None


if __name__ == '__main__':
    app = CarPlateApp()
    app.mainloop()
