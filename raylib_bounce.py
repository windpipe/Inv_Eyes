#!/usr/bin/python3
import time
import numpy as np
from PIL import Image

# 'raylib' 라이브러리의 표준 import 방식입니다.
from raylib import *

import adafruit_blinka_raspberry_pi5_piomatter as piomatter
from adafruit_blinka_raspberry_pi5_piomatter.pixelmappers import simple_multilane_mapper

# --- 하드웨어 설정 (이전과 동일) ---
panel_width = 64
panel_height = 32
panels_per_chain = 4
num_physical_chains = 3
n_addr_lines = 4

width = panel_width * panels_per_chain    # 256
height = panel_height * num_physical_chains # 96
n_lanes_for_mapper = height // (1 << n_addr_lines)  # 6

# --- 180도 회전 보정 함수 (이전과 동일) ---
def apply_rotation_fix(original_image, lane_height, num_lanes):
    corrected_img = Image.new('RGB', original_image.size)
    for i in range(num_lanes):
        box = (0, i * lane_height, original_image.width, (i + 1) * lane_height)
        strip = original_image.crop(box)
        rotated_strip = strip.transpose(Image.ROTATE_180)
        corrected_img.paste(rotated_strip, box)
    return corrected_img

# --- PioMatter 매트릭스 초기화 (이전과 동일) ---
pixelmap = simple_multilane_mapper(width, height, n_addr_lines, n_lanes_for_mapper)
geometry = piomatter.Geometry(width=width, height=height, n_addr_lines=n_addr_lines, n_planes=10, n_temporal_planes=4, map=pixelmap, n_lanes=n_lanes_for_mapper)
framebuffer = np.zeros(shape=(height, width, 3), dtype=np.uint8)
matrix = piomatter.PioMatter(colorspace=piomatter.Colorspace.RGB888Packed, pinout=piomatter.Pinout.Active3, framebuffer=framebuffer, geometry=geometry)


# ★★★★★ 이 부분이 최종 수정의 핵심입니다 ★★★★★
# --- Raylib 초기화 (존재하지 않는 set_config_flags 함수를 완전히 제거) ---
init_window(width, height, "Raylib Animation (Source)")
set_target_fps(60)

# 공의 상태를 저장할 변수
ball_position = Vector2(float(width) / 2, float(height) / 2)
ball_speed = Vector2(4.0, 3.0)
ball_radius = 10

print(f"Starting Raylib animation on {width}x{height} matrix.")
print("A small window WILL appear on your desktop. This is the intended behavior for this library.")
print("Press ESC or close the window to exit.")

# --- 메인 루프 (이전과 동일) ---
try:
    while not window_should_close():
        # 로직 업데이트
        ball_position.x += ball_speed.x
        ball_position.y += ball_speed.y

        if ball_position.x >= (width - ball_radius) or ball_position.x <= ball_radius:
            ball_speed.x *= -1.0
        if ball_position.y >= (height - ball_radius) or ball_position.y <= ball_radius:
            ball_speed.y *= -1.0

        # Raylib으로 그리기
        begin_drawing()
        clear_background(BLACK)
        draw_circle_v(ball_position, float(ball_radius), GOLD)
        draw_fps(10, 10)
        end_drawing()

        # Raylib 창을 이미지로 가져오기
        raylib_image = load_image_from_screen()
        pil_image = Image.frombytes(
            "RGBA", 
            (raylib_image.width, raylib_image.height),
            raylib_image.data
        ).convert("RGB")
        unload_image(raylib_image)

        # 180도 회전 보정
        final_output = apply_rotation_fix(pil_image, panel_height, num_physical_chains)

        # LED 매트릭스로 전송
        framebuffer[:, :] = np.array(final_output)
        matrix.show()

except KeyboardInterrupt:
    print("\nCleaning up and exiting...")

finally:
    # 프로그램 종료 시 정리
    close_window()
