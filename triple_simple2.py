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

# 설정: 64x32 패널
width = 256  # 64 * 4 (각 채널에 4개 체인)
n_lanes = 6  # 3 channels * 2 = 6 lanes for 32-pixel height
n_addr_lines = 4  # 64x32 패널은 4 address lines
height = n_lanes << n_addr_lines  # 6 << 4 = 96

canvas = Image.new('RGB', (width, height), (0, 0, 0))
draw = ImageDraw.Draw(canvas)

# 테스트 패턴 - 전체 화면을 3등분해서 각 채널 확인
# 상단 1/3 (채널 1)
draw.rectangle((10, 5, 100, 27), fill=(0, 255, 0))
draw.text((110, 10), "Channel 1", fill=(0, 255, 0))

# 중간 1/3 (채널 2)
draw.rectangle((10, 37, 100, 59), fill=(255, 0, 0))
draw.text((110, 42), "Channel 2", fill=(255, 0, 0))

# 하단 1/3 (채널 3)
draw.rectangle((10, 69, 100, 91), fill=(0, 0, 255))
draw.text((110, 74), "Channel 3", fill=(0, 0, 255))

# 체인 경계선 (64픽셀마다)
for i in range(5):
    x = i * 64
    draw.line([(x, 0), (x, height-1)], fill=(64, 64, 64))

# ⭐ 밝기 조정 (60%로 시작, 필요시 0.5~0.8 사이 조정)
enhancer = ImageEnhance.Brightness(canvas)
canvas_dimmed = enhancer.enhance(0.6)

pixelmap = simple_multilane_mapper(width, height, n_addr_lines, n_lanes)
geometry = piomatter.Geometry(
    width=width, 
    height=height, 
    n_addr_lines=n_addr_lines, 
    n_planes=10,
    n_temporal_planes=4,
    map=pixelmap, 
    n_lanes=n_lanes
)

framebuffer = np.asarray(canvas_dimmed) + 0
matrix = piomatter.PioMatter(
    colorspace=piomatter.Colorspace.RGB888Packed,
    pinout=piomatter.Pinout.Active3,
    framebuffer=framebuffer,
    geometry=geometry
)

framebuffer[:] = np.asarray(canvas_dimmed)
matrix.show()

print(f"Display: {width}x{height} ({n_lanes} lanes, {n_addr_lines} addr lines)")
print("각 채널의 밝기를 확인하세요.")
print("밝기 조정: enhance(0.5~0.8)")
input("Press enter to exit")
