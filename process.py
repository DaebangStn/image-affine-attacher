import cv2
import numpy as np
import os


def processImage(pathA, pathB, points, print_box):
    # Check if there exists images in given path
    assert os.path.exists(pathA), "Image A not found"
    assert os.path.exists(pathB), "Image B not found"

    # Check if exactly 3 points are given
    assert len(points) == 3, "Exactly 3 points are required"

    # get rectangle vertex from points by checking coordinate
    # v1 is upper left, v2 is upper right, v3 is lower left
    v1, v2, v3 = None, None, None
    points.sort(key=lambda x: x[0])

    if points[0][1] < points[1][1]:
        v1 = points[0]
        v3 = points[1]
    else:
        v1 = points[1]
        v3 = points[0]

    v2 = points[2]

    # check the orientation of the rhombus
    right_up = (v2[1] < v1[1])
    up_height = abs(v2[1] - v1[1])

    # Load images
    a = np.fromfile(pathA, np.uint8)
    b = np.fromfile(pathB, np.uint8)
    image_A = cv2.imdecode(a, cv2.IMREAD_UNCHANGED)
    image_B = cv2.imdecode(b, cv2.IMREAD_UNCHANGED)

    if image_A is None:
        print_box("포스터 이미지를 찾을 수 없습니다. 경로를 확인해 주세요")
        return None
    if image_B is None:
        print_box("키오스크 이미지를 찾을 수 없습니다. 경로를 확인해 주세요")
        return None

    print_box(f"포스터 이미지 사이즈: {image_A.shape[1]} x {image_A.shape[0]}")
    print_box(f"키오스크 이미지 사이즈: {image_B.shape[1]} x {image_B.shape[0]}")

    # Resize image A to a specific pixel size
    new_width = v2[0] - v1[0]  # New width in pixels
    new_height = v3[1] - v1[1]  # New height in pixels
    dim = (new_width, new_height)
    image_A_resized = cv2.resize(image_A, dim, interpolation=cv2.INTER_AREA)

    # Define points for affine transformation
    # Points are selected such that a rectangular perspective is transformed into a rhombus
    pts1 = np.float32([[0, 0], [new_width, 0], [0, new_height]])

    if right_up:
        pts2 = np.float32([[0, up_height], [new_width, 0], [0, new_height + up_height]])
    else:
        pts2 = np.float32([[0, 0], [new_width, up_height], [0, new_height]])

    matrix = cv2.getAffineTransform(pts1, pts2)

    # Apply affine transformation and border replication to create a new image with a larger size
    image_A_transformed = cv2.warpAffine(image_A_resized, matrix, (new_width, new_height + up_height),
                                         borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))

    # Check if image B has an alpha channel (transparency)
    if image_B.shape[2] == 4:
        # If it has an alpha channel, split it from the color channels
        B_color = image_B[:, :, 0:3]
        B_alpha = image_B[:, :, 3]
    else:
        B_color = image_B
        B_alpha = np.ones(B_color.shape[0:2], dtype=B_color.dtype) * 255

    # Calculate coordinates where the transformed image will be placed in image B
    x_offset = v1[0]
    y_offset = min(v1[1], v2[1])

    # Define the region of interest in image B such that it doesn't exceed the image's dimensions
    roi_height = min(new_height + up_height, B_color.shape[0] - y_offset)
    roi_width = min(new_width, B_color.shape[1] - x_offset)

    # Resize 'masked' to match the dimensions of the region of interest in image B
    masked_resized = cv2.resize(image_A_transformed, (roi_width, roi_height))

    # Create an alpha channel for the resized transformed image A if it doesn't have one
    if masked_resized.shape[2] == 3:
        alpha_channel = np.ones(masked_resized.shape[0:2], dtype=masked_resized.dtype) * 255
        masked_resized = cv2.merge([masked_resized, alpha_channel])

    # Separate the color and alpha channels of the resized transformed image A
    A_color = masked_resized[:, :, 0:3]

    # Create an alpha channel for the transformed image based on where the image is not black
    A_alpha = np.all(A_color == [0, 0, 0], axis=2)

    # Bitwise AND the alpha channels with the image regions
    roi_A_masked = cv2.bitwise_and(A_color, A_color, mask=cv2.bitwise_not(A_alpha.astype(np.uint8) * 255))
    roi_B_masked = np.zeros_like(B_color[y_offset:y_offset + roi_height, x_offset:x_offset + roi_width])
    for i in range(3):  # Number of color channels
        roi_B_masked[:, :, i] = cv2.bitwise_and(
            B_color[y_offset:y_offset + roi_height, x_offset:x_offset + roi_width][:, :, i],
            B_color[y_offset:y_offset + roi_height, x_offset:x_offset + roi_width][:, :, i],
            mask=A_alpha.astype(np.uint8) * 255)

    # Combine the image regions
    roi_combined = cv2.add(roi_A_masked, roi_B_masked)

    # Update the color and alpha channels of image B
    B_color[y_offset:y_offset + roi_height, x_offset:x_offset + roi_width] = roi_combined

    # Merge the color and alpha channels into the final image
    image_B_final = cv2.merge([B_color, B_alpha])

    return image_B_final
