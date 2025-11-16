#!/usr/bin/python3
import time
import numpy as np
from PIL import Image
import cv2

import adafruit_blinka_raspberry_pi5_piomatter as piomatter
from adafruit_blinka_raspberry_pi5_piomatter.pixelmappers import simple_multilane_mapper

# --- 하드웨어 설정 ---
panel_width = 64
panel_height = 32
panels_per_chain = 4
num_physical_chains = 3
n_addr_lines = 4

width = panel_width * panels_per_chain    # 256
height = panel_height * num_physical_chains # 96
n_lanes_for_mapper = height // (1 << n_addr_lines)  # 6

# --- 180도 회전 보정 함수 ---
def apply_rotation_fix(original_image, lane_height, num_lanes):
    corrected_img = Image.new('RGB', original_image.size)
    for i in range(num_lanes):
        box = (0, i * lane_height, original_image.width, (i + 1) * lane_height)
        strip = original_image.crop(box)
        rotated_strip = strip.transpose(Image.ROTATE_180)
        corrected_img.paste(rotated_strip, box)
    return corrected_img

# --- PioMatter 매트릭스 초기화 ---
pixelmap = simple_multilane_mapper(width, height, n_addr_lines, n_lanes_for_mapper)
geometry = piomatter.Geometry(
    width=width, 
    height=height, 
    n_addr_lines=n_addr_lines, 
    n_planes=10, 
    n_temporal_planes=4, 
    map=pixelmap, 
    n_lanes=n_lanes_for_mapper
)
framebuffer = np.zeros(shape=(height, width, 3), dtype=np.uint8)
matrix = piomatter.PioMatter(
    colorspace=piomatter.Colorspace.RGB888Packed, 
    pinout=piomatter.Pinout.Active3, 
    framebuffer=framebuffer, 
    geometry=geometry
)

# 공의 상태
ball_x = width / 2.0
ball_y = height / 2.0
ball_speed_x = 4.0
ball_speed_y = 3.0
ball_radius = 10
ball_color = (0, 215, 255)  # GOLD in BGR (OpenCV uses BGR!)

print(f"Starting animation on {width}x{height} matrix.")
print("Press Ctrl-C to exit.")

# --- 메인 루프 ---
try:
    while True:
        # 로직 업데이트
        ball_x += ball_speed_x
        ball_y += ball_speed_y
        
        if ball_x >= (width - ball_radius) or ball_x <= ball_radius:
            ball_speed_x *= -1.0
        if ball_y >= (height - ball_radius) or ball_y <= ball_radius:
            ball_speed_y *= -1.0
        
        # 화면 지우기 (검은색)
        temp_buffer = np.zeros((height, width, 3), dtype=np.uint8)
        
        # === 텍스트 및 도형 추가 ===
        
        # 1. 상단에 텍스트 추가
        cv2.putText(temp_buffer, "Fantasy Inventory - ACC Children", (10, 15), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        
        # 2. 테두리 사각형
        cv2.rectangle(temp_buffer, (2, 2), (width-3, height-3), (0, 255, 0), 2)
        
        # 3. 중앙 십자선
        cv2.line(temp_buffer, (width//2, 0), (width//2, height), (50, 50, 50), 1)
        cv2.line(temp_buffer, (0, height//2), (width, height//2), (50, 50, 50), 1)
        
        # 4. 하단에 작은 사각형들
        cv2.rectangle(temp_buffer, (20, height-25), (50, height-10), (255, 0, 0), -1)
        cv2.rectangle(temp_buffer, (60, height-25), (90, height-10), (0, 255, 0), -1)
        cv2.rectangle(temp_buffer, (100, height-25), (130, height-10), (0, 0, 255), -1)
        
        # 5. 우상단에 작은 원
        cv2.circle(temp_buffer, (width-20, 20), 8, (255, 0, 255), 2)
        
        # 6. 대각선
        cv2.line(temp_buffer, (0, 0), (50, 50), (128, 128, 0), 2)
        
        # === 공 그리기 (기존) ===
        cv2.circle(temp_buffer, (int(ball_x), int(ball_y)), ball_radius, ball_color, -1)
        
        # OpenCV는 BGR, PIL은 RGB이므로 변환
        temp_buffer_rgb = cv2.cvtColor(temp_buffer, cv2.COLOR_BGR2RGB)
        
        # 180도 회전 보정
        # final_output = apply_rotation_fix(Image.fromarray(temp_buffer_rgb), panel_height, num_physical_chains)
        
        # LED 매트릭스로 전송
        framebuffer[:, :] = np.array(temp_buffer_rgb)
        matrix.show()
        
        time.sleep(1/60)  # 60 FPS

except KeyboardInterrupt:
    print("\nExiting...")