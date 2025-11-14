#!/usr/bin/python3
# SPDX-FileCopyrightText: 2025 Tim Cocks for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
Display a simple test pattern on twelve 64x32 matrix panels
using Active3 (Triple Bonnet) connections.
4 panels chained on each of 3 channels = 256x96 total
"""
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance
import adafruit_blinka_raspberry_pi5_piomatter as piomatter
from adafruit_blinka_raspberry_pi5_piomatter.pixelmappers import simple_multilane_mapper

# 설정: 64x32 패널 × 4개 체인 = 256 wide, 3 채널 = 96 high
width = 256  # 64 * 4 (4개 패널 체인)
n_lanes = 3  # Triple Bonnet의 3개 채널
n_addr_lines = 4  # 64x32 패널은 4 address lines (not 5!)
height = 32 * n_lanes  # 32 * 3 = 96

canvas = Image.new('RGB', (width, height), (0, 0, 0))
draw = ImageDraw.Draw(canvas)

# 테스트 패턴 그리기
# 각 채널마다 다른 색상으로 테스트
# 채널 1 (상단 32줄)
draw.rectangle((10, 5, 100, 27), fill=(0, 255, 0))  # 초록
draw.text((110, 10), "CH1", fill=(0, 255, 0))

# 채널 2 (중간 32줄)
draw.rectangle((10, 37, 100, 59), fill=(255, 0, 0))  # 빨강
draw.text((110, 42), "CH2", fill=(255, 0, 0))

# 채널 3 (하단 32줄)
draw.rectangle((10, 69, 100, 91), fill=(0, 0, 255))  # 파랑
draw.text((110, 74), "CH3", fill=(0, 0, 255))

# 각 체인 구간 표시 (256을 4등분)
for i in range(5):
    x = i * 64
    draw.line([(x, 0), (x, height)], fill=(128, 128, 128))

# ⭐ 밝기 조정 (플리커/밝기 문제 완화)
enhancer = ImageEnhance.Brightness(canvas)
canvas_dimmed = enhancer.enhance(0.6)  # 60% 밝기 (0.5~0.8 사이로 조정)

pixelmap = simple_multilane_mapper(width, height, n_addr_lines, n_lanes)
geometry = piomatter.Geometry(
    width=width, 
    height=height, 
    n_addr_lines=n_addr_lines, 
    n_planes=10,  # 기본값 유지
    n_temporal_planes=4,  # 기본값 유지
    map=pixelmap, 
    n_lanes=n_lanes
)

framebuffer = np.asarray(canvas_dimmed) + 0  # 밝기 조정된 이미지 사용
matrix = piomatter.PioMatter(
    colorspace=piomatter.Colorspace.RGB888Packed,
    pinout=piomatter.Pinout.Active3,
    framebuffer=framebuffer,
    geometry=geometry
)

framebuffer[:] = np.asarray(canvas_dimmed)
matrix.show()

print("Display active. 각 채널과 체인 경계를 확인하세요.")
print("밝기가 너무 어두우면 enhance(0.7~0.8)로 올리세요.")
input("Press enter to exit")
