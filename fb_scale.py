#!/usr/bin/python3
"""
(설명 주석은 생략)
"""
import time
import click
import numpy as np
import PIL.Image as Image

import adafruit_blinka_raspberry_pi5_piomatter as piomatter
from adafruit_blinka_raspberry_pi5_piomatter.pixelmappers import simple_multilane_mapper

# --- 1. 사용자님의 '기본 소스'에서 가져온 하드웨어 설정 ---
panel_width = 64
panel_height = 32
panels_per_chain = 4
num_physical_chains = 3
n_addr_lines = 4

# --- 2. '기본 소스'와 동일하게 전체 디스플레이 크기 및 '속임수' 값 계산 ---
width = panel_width * panels_per_chain    # 256
height = panel_height * num_physical_chains # 96
n_lanes_for_mapper = height // (1 << n_addr_lines)  # 96 // 16 = 6

# --- 3. 프레임버퍼 미러링을 위한 추가 설정 ---
# 이 값들을 수정하여 화면의 어느 부분을, 얼마나 축소해서 보여줄지 결정할 수 있습니다.
xoffset = 0   # 화면 왼쪽 끝에서 얼마나 떨어져서 시작할지
yoffset = 0   # 화면 위쪽 끝에서 얼마나 떨어져서 시작할지
scale = 4     # 화면을 얼마나 축소할지 (숫자가 클수록 더 많이 축소)

# --- (여기부터는 원본 소스와 거의 동일) ---
with open("/sys/class/graphics/fb0/virtual_size") as f:
    screenx, screeny = [int(word) for word in f.read().split(",")]

with open("/sys/class/graphics/fb0/bits_per_pixel") as f:
    bits_per_pixel = int(f.read())
assert bits_per_pixel in (16, 32)
bytes_per_pixel = bits_per_pixel // 8
dtype = {2: np.uint16, 4: np.uint32}[bytes_per_pixel]

with open("/sys/class/graphics/fb0/stride") as f:
    stride = int(f.read())

linux_framebuffer = np.memmap('/dev/fb0',mode='r', shape=(screeny, stride // bytes_per_pixel), dtype=dtype)

# --- 4. '기본 소스'의 회전 문제 해결 로직을 그대로 가져옴 ---
def apply_rotation_fix(original_image, lane_height, num_lanes):
    corrected_img = Image.new('RGB', original_image.size)
    for i in range(num_lanes):
        box = (0, i * lane_height, original_image.width, (i + 1) * lane_height)
        strip = original_image.crop(box)
        rotated_strip = strip.transpose(Image.ROTATE_180)
        corrected_img.paste(rotated_strip, box)
    return corrected_img

# --- 5. PioMatter 객체 설정 (하드코딩된 값 사용) ---
pixelmap = simple_multilane_mapper(width, height, n_addr_lines, n_lanes_for_mapper)
geometry = piomatter.Geometry(width=width, height=height, n_addr_lines=n_addr_lines, n_planes=10, n_temporal_planes=4, map=pixelmap, n_lanes=n_lanes_for_mapper)
matrix_framebuffer = np.zeros(shape=(geometry.height, geometry.width, 3), dtype=np.uint8)
matrix = piomatter.PioMatter(colorspace=piomatter.Colorspace.RGB888Packed, pinout=piomatter.Pinout.Active3, framebuffer=matrix_framebuffer, geometry=geometry)

print(f"Matrix size: {width}x{height}. Mirroring screen region at ({xoffset},{yoffset}) with {scale}x scale.")
print("Press Ctrl-C to exit.")

# --- 6. 메인 루프 (회전 문제 해결 로직 추가) ---
try:
    while True:
        # 리눅스 프레임버퍼에서 원하는 영역을 잘라냄
        source_width = width * scale
        source_height = height * scale
        tmp = linux_framebuffer[yoffset:yoffset + source_height, xoffset:xoffset + source_width]

        # 색상 변환 (RGB565 -> RGB888)
        if bits_per_pixel == 16:
            r = (tmp & 0xf800) >> 8; r = r | (r >> 5); r = r.astype(np.uint8)
            g = (tmp & 0x07e0) >> 3; g = g | (g >> 6); g = g.astype(np.uint8)
            b = (tmp & 0x001f) << 3; b = b | (b >> 5); b = b.astype(np.uint8)
            img = Image.fromarray(np.stack([r, g, b], -1))
        else: # 32bpp
            img = Image.fromarray(tmp.astype(np.uint8)).convert('RGB')

        # 이미지 크기를 매트릭스 크기에 맞게 리사이즈
        img = img.resize((width, height))

        # ★★★★★ 이 부분이 핵심 ★★★★★
        # 리사이즈된 이미지에 180도 회전 보정을 적용
        final_output = apply_rotation_fix(img, panel_height, num_physical_chains)

        # 보정된 최종 이미지를 매트릭스 프레임버퍼에 복사
        matrix_framebuffer[:, :] = np.array(final_output)
        matrix.show()
        time.sleep(0.01) # CPU 사용량을 줄이기 위해 약간의 딜레이 추가

except KeyboardInterrupt:
    print("\nExiting...")
