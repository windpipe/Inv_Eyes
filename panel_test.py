#!/usr/bin/python3

import time
import math
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

# --- 회전하는 막대기 아이콘 그리기 함수 ---
def draw_rotating_icon(canvas, center_x, center_y, big_radius, sun_radius, angle_offset, num_rays=8):
    """
    회전하는 막대기 아이콘을 그립니다.
    
    Args:
        canvas: 그릴 numpy array (BGR)
        center_x, center_y: 큰 원의 중심
        big_radius: 큰 원의 반지름
        sun_radius: 작은 원(막대 중심)의 반지름
        angle_offset: 회전 각도
        num_rays: 막대 개수
    """
    # 큰 검은 원 그리기
    cv2.circle(canvas, (center_x, center_y), big_radius, (20, 20, 20), -1)
    
    # 안쪽 작은 검은 원 (막대 중심)
    sun_center_x = center_x + int(big_radius * 0.45)
    sun_center_y = center_y - int(big_radius * 0.45)
    cv2.circle(canvas, (sun_center_x, sun_center_y), sun_radius, (20, 20, 20), -1)
    
    # 회전하는 흰 막대들
    inner_r = sun_radius + 2
    outer_r = sun_radius + 12
    thickness = 3
    
    for i in range(num_rays):
        angle = 2 * math.pi * i / num_rays + angle_offset
        
        x1 = int(sun_center_x + inner_r * math.cos(angle))
        y1 = int(sun_center_y + inner_r * math.sin(angle))
        x2 = int(sun_center_x + outer_r * math.cos(angle))
        y2 = int(sun_center_y + outer_r * math.sin(angle))
        
        cv2.line(canvas, (x1, y1), (x2, y2), (255, 255, 255), thickness, cv2.LINE_AA)

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

# 애니메이션 상태
angle_offset = 0
bg_is_white = True  # 배경색 토글

# 두 아이콘의 위치 및 크기 설정
icon1_center = (80, height // 2)   # 왼쪽 아이콘
icon2_center = (176, height // 2)  # 오른쪽 아이콘
icon_radius = 38  # 큰 원의 반지름
sun_radius = 11   # 작은 원의 반지름

print(f"Starting animation on {width}x{height} matrix.")
print("Press Ctrl-C to exit.")

# --- 메인 루프 ---
try:
    while True:
        # 배경색 설정
        bg_color = 255 if bg_is_white else 0
        
        # 화면 지우기 (배경색)
        temp_buffer = np.full((height, width, 3), bg_color, dtype=np.uint8)
        
        # 첫 번째 아이콘 그리기 (왼쪽)
        draw_rotating_icon(
            temp_buffer, 
            icon1_center[0], 
            icon1_center[1], 
            icon_radius, 
            sun_radius, 
            angle_offset
        )
        
        # 두 번째 아이콘 그리기 (오른쪽, 반대 방향 회전)
        draw_rotating_icon(
            temp_buffer, 
            icon2_center[0], 
            icon2_center[1], 
            icon_radius, 
            sun_radius, 
            -angle_offset  # 반대 방향
        )
        
        # OpenCV는 BGR, PIL은 RGB이므로 변환
        temp_buffer_rgb = cv2.cvtColor(temp_buffer, cv2.COLOR_BGR2RGB)
        
        # 180도 회전 보정 (필요시 활성화)
        # final_output = apply_rotation_fix(Image.fromarray(temp_buffer_rgb), panel_height, num_physical_chains)
        
        # LED 매트릭스로 전송
        framebuffer[:, :] = np.array(temp_buffer_rgb)
        matrix.show()
        
        # 각도 업데이트 (회전 속도)
        angle_offset += 0.05
        
        time.sleep(1/60)  # 60 FPS

except KeyboardInterrupt:
    print("\nExiting...")

