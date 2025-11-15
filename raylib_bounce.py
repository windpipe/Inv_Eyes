#!/usr/bin/python3
import time
import numpy as np
from PIL import Image, ImageFont

# 1. Raylib 라이브러리 import (pyray라는 이름으로 사용)
import pyray

import adafruit_blinka_raspberry_pi5_piomatter as piomatter
from adafruit_blinka_raspberry_pi5_piomatter.pixelmappers import simple_multilane_mapper

# --- '기본 소스'에서 확립된 모든 하드웨어 설정을 그대로 가져옵니다 ---
panel_width = 64
panel_height = 32
panels_per_chain = 4
num_physical_chains = 3
n_addr_lines = 4

width = panel_width * panels_per_chain    # 256
height = panel_height * num_physical_chains # 96
n_lanes_for_mapper = height // (1 << n_addr_lines)  # 96 // 16 = 6

# --- 이전에 완성한 180도 회전 보정 함수를 그대로 가져옵니다 ---
def apply_rotation_fix(original_image, lane_height, num_lanes):
    corrected_img = Image.new('RGB', original_image.size)
    for i in range(num_lanes):
        box = (0, i * lane_height, original_image.width, (i + 1) * lane_height)
        strip = original_image.crop(box)
        rotated_strip = strip.transpose(Image.ROTATE_180)
        corrected_img.paste(rotated_strip, box)
    return corrected_img

# --- PioMatter 매트릭스 초기화 (이 부분도 '기본 소스'와 동일) ---
pixelmap = simple_multilane_mapper(width, height, n_addr_lines, n_lanes_for_mapper)
geometry = piomatter.Geometry(width=width, height=height, n_addr_lines=n_addr_lines, n_planes=10, n_temporal_planes=4, map=pixelmap, n_lanes=n_lanes_for_mapper)
framebuffer = np.zeros(shape=(height, width, 3), dtype=np.uint8) # RGB888이므로 3채널
matrix = piomatter.PioMatter(colorspace=piomatter.Colorspace.RGB888Packed, pinout=piomatter.Pinout.Active3, framebuffer=framebuffer, geometry=geometry)

# --- Raylib 초기화 및 설정 ---
# CONFIG_FLAG_WINDOW_HIDDEN 플래그로 데스크톱에 창이 보이지 않게 합니다.
pyray.set_config_flags(pyray.ConfigFlags.FLAG_WINDOW_HIDDEN)
pyray.init_window(width, height, "Raylib Offscreen Canvas")
pyray.set_target_fps(60) # 초당 60프레임으로 부드럽게

# 공의 상태를 저장할 변수
ball_position = pyray.Vector2(float(width) / 2, float(height) / 2)
ball_speed = pyray.Vector2(4.0, 3.0)
ball_radius = 10

print(f"Starting Raylib animation on {width}x{height} matrix.")
print("Press Ctrl-C to exit.")

# --- 메인 루프 ---
try:
    # Raylib 창이 닫히라는 신호를 받기 전까지 계속 반복
    while not pyray.window_should_close():
        # --- 1. 로직 업데이트 (공 움직이기) ---
        ball_position.x += ball_speed.x
        ball_position.y += ball_speed.y

        # 화면 경계에 부딪혔는지 확인하고 방향 바꾸기
        if ball_position.x >= (width - ball_radius) or ball_position.x <= ball_radius:
            ball_speed.x *= -1.0
        if ball_position.y >= (height - ball_radius) or ball_position.y <= ball_radius:
            ball_speed.y *= -1.0

        # --- 2. Raylib으로 그림 그리기 ---
        pyray.begin_drawing()
        pyray.clear_background(pyray.BLACK)
        pyray.draw_circle_v(ball_position, float(ball_radius), pyray.GOLD)
        pyray.draw_fps(10, 10) # FPS 표시 (LED에도 보임)
        pyray.end_drawing()

        # --- 3. Raylib 창을 '스크린샷'하여 이미지 데이터로 가져오기 ---
        raylib_image = pyray.load_image_from_screen()
        # Raylib 이미지는 RGBA(4채널)이므로 RGB(3채널)로 변환
        pyray.image_format(raylib_image, pyray.PixelFormat.PIXELFORMAT_UNCOMPRESSED_R8G8B8)
        
        # Pillow Image 객체로 변환
        # (주의: pyray.image_to_string은 버그가 있을 수 있어 get_image_data를 사용)
        pil_image = Image.frombytes(
            "RGB",
            (raylib_image.width, raylib_image.height),
            pyray.get_image_data(raylib_image)
        )
        
        # 사용이 끝난 Raylib 이미지는 메모리에서 해제 (매우 중요!)
        pyray.unload_image(raylib_image)

        # --- 4. 180도 회전 보정 적용 ---
        final_output = apply_rotation_fix(pil_image, panel_height, num_physical_chains)

        # --- 5. 최종 이미지를 PioMatter 프레임버퍼로 전송 ---
        framebuffer[:, :] = np.array(final_output)
        matrix.show()

except KeyboardInterrupt:
    print("\nCleaning up and exiting...")

finally:
    # --- 프로그램 종료 시 정리 ---
    pyray.close_window()
