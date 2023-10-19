import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw
from process import processImage
import cv2
import os
import numpy as np


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("키오스크 이미지 합성")
        self.root.geometry("1200x800")
        self.points = []

        # Create two canvases for image display
        self.canvas1 = tk.Canvas(self.root, width=500, height=800)
        self.canvas1.pack(side="left", fill="both", expand=True)
        self.canvas2 = tk.Canvas(self.root, width=500, height=800)
        self.canvas2.pack(side="left", fill="both", expand=True)

        # Create frames to hold the image labels
        self.frame1 = tk.Frame(self.canvas1)
        self.canvas1.create_window((0, 0), window=self.frame1, anchor="nw")
        self.frame2 = tk.Frame(self.canvas2)
        self.canvas2.create_window((0, 0), window=self.frame2, anchor="nw")

        self.frame3 = tk.Frame(self.root, width=200, height=800)
        self.frame3.pack_propagate(False)
        self.frame3.pack(side="left", fill="both", expand=True)

        # Add the image labels to the frames
        self.img_label1 = tk.Label(self.frame1, text="키오스크 이미지 원본")
        self.img_label1.pack()
        self.img_label2 = tk.Label(self.frame2, text="이미지 처리 결과")
        self.img_label2.pack()

        # Buttons for image selection
        self.button_A = tk.Button(self.frame3, text="포스터 이미지 선택", command=self.load_image_A, height=2)
        self.button_A.pack(fill=tk.X)
        self.button_B = tk.Button(self.frame3, text="키오스크 이미지 선택", command=self.load_image_B, height=2)
        self.button_B.pack(fill=tk.X)

        # Button for selection reset
        self.button_reset = tk.Button(self.frame3, text="붙일 좌표 선택 취소", command=self.reset_selection, height=2)
        self.button_reset.pack(fill=tk.X)

        # Button for image processing
        self.button_process = tk.Button(self.frame3, text="포스터 붙이기", command=self.process_images, height=2)
        self.button_process.pack(fill=tk.X)

        # Button for image processing
        self.button_save = tk.Button(self.frame3, text="결과 저장", command=self.save_image, height=2)
        self.button_save.pack(fill=tk.X)

        self.frame4 = tk.Frame(self.frame3)
        self.frame4.pack(fill=tk.BOTH, expand=True)

        # Create a Text widget for the logs
        self.text_box = tk.Text(self.frame4, wrap='word')
        self.text_box.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        # Create a Scrollbar for the Text widget
        scrollbar = tk.Scrollbar(self.frame4, command=self.text_box.yview, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, expand=True)

        # Configure the Text widget to use the Scrollbar
        self.text_box.config(yscrollcommand=scrollbar.set)

        # Paths for image files
        self.path_A = None
        self.path_B = None
        self.img_B = None
        self.points = []
        self.img_processed = None

    def load_image_A(self):
        self.path_A = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.png")])
        if self.path_A:
            self.print_box(f"포스터 이미지 경로: {self.path_A}")

    def load_image_B(self):
        self.path_B = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.png")])
        if self.path_B:
            self.print_box(f"키오스크 이미지 경로: {self.path_B}")
            self.img_B = Image.open(self.path_B)
            self.display_image1(self.img_B)
            self.reset_selection()
            self.root.bind("<Button-1>", self.click_event)

    def click_event(self, event):
        x, y = event.x, event.y
        self.points.append((x, y))
        self.print_box(f"선택한 위치: {x, y}")
        if len(self.points) == 3:
            self.root.unbind("<Button-1>")
        self.draw_points()

    def draw_points(self):
        img_copy = self.img_B.copy()
        draw = ImageDraw.Draw(img_copy)
        for point in self.points:
            draw.ellipse((point[0]-2, point[1]-2, point[0]+2, point[1]+2), fill="green")
        self.display_image1(img_copy)

    def reset_selection(self):
        self.points = []
        self.display_image1(self.img_B)
        self.root.bind("<Button-1>", self.click_event)

    def process_images(self):
        if self.path_A and self.path_B and len(self.points) == 3:
            self.img_processed = processImage(self.path_A, self.path_B, self.points, self.print_box)
            self.display_image2(self.img_processed)
            self.print_box("이미지 붙이기 완료")
        else:
            messagebox.showerror("Error", "포스터와 키오스크 이미지, 3개의 점을 선택해주세요.")

    def save_image(self):
        if self.img_processed is not None:
            save_path = filedialog.asksaveasfilename(filetypes=[("Image files", "*.jpg *.png")],
                                                     defaultextension=".png")
            if save_path is not None:
                ext = os.path.splitext(save_path)[1]
                result, n = cv2.imencode(ext, self.img_processed, None)

                if result:
                    with open(save_path, mode='w+b') as f:
                        n.tofile(f)
                    self.print_box(f"이미지 저장 경로: {save_path}")
                else:
                    messagebox.showerror("Error", "이미지 저장에 실패했습니다.")
        else:
            messagebox.showerror("Error", "포스터를 먼저 붙여주세요.")

    def display_image1(self, img):
        img_tk = ImageTk.PhotoImage(img)
        self.img_label1.config(image=img_tk)
        self.img_label1.image = img_tk

        # Update the scroll region after displaying the image
        self.frame1.update_idletasks()
        self.canvas1.configure(scrollregion=self.canvas1.bbox('all'))

    def display_image2(self, img):
        img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGBA))
        img_tk = ImageTk.PhotoImage(img_pil)
        self.img_label2.config(image=img_tk)
        self.img_label2.image = img_tk

        # Update the scroll region after displaying the image
        self.frame2.update_idletasks()
        self.canvas2.configure(scrollregion=self.canvas2.bbox('all'))

    def print_box(self, text):
        # Append the text to the Text widget
        self.text_box.insert(tk.END, text + '\n')

        # Scroll the Text widget to the end
        self.text_box.see(tk.END)
