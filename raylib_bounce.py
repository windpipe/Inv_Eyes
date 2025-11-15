#!/usr/bin/python3
import time
import numpy as np
from PIL import Image

# 1. 'raylib' 라이브러리를 rl 이라는 이름으로 import 합니다.
import raylib as rl

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

# --- PioMatter 매트릭스 초기화 ---
pixelmap = simple_multilane_mapper(width, height, n_addr_lines, n_lanes_for_mapper)
geometry = piomatter.Geometry(width=width, height=height, n_addr_lines=n_addr_lines, n_planes=10, n_temporal_planes=4, map=pixelmap, n_lanes=n_lanes_for_mapper)
framebuffer = np.zeros(shape=(height, width, 3), dtype=np.uint8)
matrix = piomatter.PioMatter(colorspace=piomatter.Colorspace.RGB888Packed, pinout=piomatter.Pinout.Active3, framebuffer=framebuffer, geometry=geometry)

# --- Raylib 초기화 및 설정 ('raylib' 문법에 맞게 수정) ---
# ★★★ 핵심 1: SetConfigFlags 함수는 rl.set_config_flags로 호출합니다. ★★★
rl.set_config_flags(rl.ConfigFlags.FLAG_WINDOW_HIDDEN)
rl.init_window(width, height, "Raylib Offscreen Canvas")
rl.set_target_fps(60)

# 공의 상태를 저장할 변수
# Vector2는 rl.Vector2 로 접근해야 합니다.
ball_position = rl.Vector2(float(width) / 2, float(height) / 2)
ball_speed = rl.Vector2(4.0, 3.0)
ball_radius = 10
# 색상도 rl.GOLD 처럼 접근해야 합니다.
ball_color = rl.GOLD

print(f"Starting Raylib animation on {width}x{height} matrix.")
print("Press Ctrl-C to exit.")

# --- 메인 루프 ---
try:
    while not rl.window_should_close():
        # --- 1. 로직 업데이트 ---
        ball_position.x += ball_speed.x
        ball_position.y += ball_speed.y

        if ball_position.x >= (width - ball_radius) or ball_position.x <= ball_radius:
            ball_speed.x *= -1.0
        if ball_position.y >= (height - ball_radius) or ball_position.y <= ball_radius:
            ball_speed.y *= -1.0

        # --- 2. Raylib으로 그림 그리기 (모든 함수 앞에 rl. 추가) ---
        rl.begin_drawing()
        rl.clear_background(rl.BLACK)
        rl.draw_circle_v(ball_position, float(ball_radius), ball_color)
        rl.draw_fps(10, 10)
        rl.end_drawing()

        # --- 3. Raylib 창을 이미지 데이터로 가져오기 ---
        raylib_image = rl.load_image_from_screen()
        
        # ★★★ 핵심 2: 'raylib' 패키지에서는 이미지 데이터를 이렇게 가져옵니다. ★★★
        # ctypes 포인터인 image.data를 바로 Pillow로 넘깁니다.
        pil_image = Image.frombytes(
            "RGBA", # LoadImageFromScreen은 항상 RGBA 형식을 반환합니다.
            (raylib_image.width, raylib_image.height),
            raylib_image.data
        ).convert("RGB") # LED 매트릭스에 맞는 RGB 형식으로 최종 변환합니다.
        
        rl.unload_image(raylib_image)

        # --- 4. 180도 회전 보정 적용 ---
        final_output = apply_rotation_fix(pil_image, panel_height, num_physical_chains)

        # --- 5. 최종 이미지를 PioMatter 프레임버퍼로 전송 ---
        framebuffer[:, :] = np.array(final_output)
        matrix.show()

except KeyboardInterrupt:
    print("\nCleaning up and exiting...")

finally:
    # --- 프로그램 종료 시 정리 ---
    rl.close_window()
