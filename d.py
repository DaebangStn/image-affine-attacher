from pathlib import Path
import cv2
import numpy as np

pathA = 'C:\\Users\\geon\\Desktop\\몰 루!\\blank.png'
n = np.fromfile(pathA, np.uint8)
image_A = cv2.imdecode(n, cv2.IMREAD_UNCHANGED)
