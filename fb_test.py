#!/usr/bin/python3
"""
(설명 주석은 생략)
"""
import time
import click
import numpy as np

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

# --- 3. 프레임버퍼 미러링 위치 설정 ---
# 이 값들을 수정하여 데스크톱 화면의 어느 256x96 영역을 보여줄지 결정합니다.
xoffset = 100   # 화면 왼쪽 끝에서 얼마나 떨어져서 시작할지
yoffset = 100   # 화면 위쪽 끝에서 얼마나 떨어져서 시작할지

# --- (여기부터는 원본 소스와 거의 동일) ---
with open("/sys/class/graphics/fb0/virtual_size") as f:
    screenx, screeny = [int(word) for word in f.read().split(",")]

with open("/sys/class/graphics/fb0/bits_per_pixel") as f:
    bits_per_pixel = int(f.read())
assert bits_per_pixel in (16, 32) # 16bpp 또는 32bpp 지원
bytes_per_pixel = bits_per_pixel // 8
dtype = np.uint16 if bits_per_pixel == 16 else np.uint32

with open("/sys/class/graphics/fb0/stride") as f:
    stride = int(f.read())

linux_framebuffer = np.memmap('/dev/fb0',mode='r', shape=(screeny, stride // bytes_per_pixel), dtype=dtype)

# ★★★★★ 핵심 1: Numpy를 이용한 180도 회전 보정 함수 ★★★★★
def apply_rotation_fix_numpy(source_array, lane_height, num_lanes):
    # 수정된 데이터를 담을 똑같은 크기의 빈 배열 생성
    corrected_array = np.zeros_like(source_array)
    
    for i in range(num_lanes):
        # 각 채널의 영역을 정의 (세로 시작, 세로 끝)
        start_y = i * lane_height
        end_y = (i + 1) * lane_height
        
        # 해당 영역(채널)을 잘라냅니다.
        strip = source_array[start_y:end_y, :]
        
        # 잘라낸 조각을 Numpy를 이용해 180도 회전시킵니다. (k=2는 90도씩 두번)
        rotated_strip = np.rot90(strip, k=2)
        
        # 회전된 조각을 새 배열의 원래 위치에 붙여넣습니다.
        corrected_array[start_y:end_y, :] = rotated_strip
        
    return corrected_array

# --- 5. PioMatter 객체 설정 (하드코딩된 값 사용) ---
pixelmap = simple_multilane_mapper(width, height, n_addr_lines, n_lanes_for_mapper)
geometry = piomatter.Geometry(width=width, height=height, n_addr_lines=n_addr_lines, n_planes=10, n_temporal_planes=4, map=pixelmap, n_lanes=n_lanes_for_mapper)
# 이 스크립트는 RGB565를 사용하므로, framebuffer의 dtype도 uint16이어야 합니다.
framebuffer = np.zeros(shape=(geometry.height, geometry.width), dtype=np.uint16)
matrix = piomatter.PioMatter(colorspace=piomatter.Colorspace.RGB565, pinout=piomatter.Pinout.Active3, framebuffer=framebuffer, geometry=geometry)

print(f"Matrix size: {width}x{height}. Mirroring 1:1 screen region at ({xoffset},{yoffset}).")
print("Press Ctrl-C to exit.")

# --- 6. 메인 루프 (Numpy 회전 보정 로직 추가) ---
try:
    while True:
        # 리눅스 프레임버퍼에서 256x96 영역을 잘라냄
        source_region = linux_framebuffer[yoffset:yoffset+height, xoffset:xoffset+width]

        # ★★★★★ 핵심 2: 32bpp(풀컬러) -> 16bpp(RGB565) 변환 ★★★★★
        if bits_per_pixel == 32:
            r = ((source_region >> 16) & 0xFF).astype(np.uint16)
            g = ((source_region >> 8) & 0xFF).astype(np.uint16)
            b = (source_region & 0xFF).astype(np.uint16)
            source_region_16bpp = ((r & 0b11111000) << 8) | ((g & 0b11111100) << 3) | (b >> 3)
        else: # 16bpp
            source_region_16bpp = source_region

        # ★★★★★ 핵심 3: Numpy 회전 보정 함수를 호출 ★★★★★
        corrected_region = apply_rotation_fix_numpy(source_region_16bpp, panel_height, num_physical_chains)
        
        # 보정된 최종 데이터를 매트릭스 프레임버퍼에 복사
        framebuffer[:,:] = corrected_region
        matrix.show()
        time.sleep(0.01) # CPU 사용량을 줄이기 위해 약간의 딜레이 추가

except KeyboardInterrupt:
    print("\nExiting...")
