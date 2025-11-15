#!/usr/bin/python3
# SPDX-FileCopyrightText: 2025 Tim Cocks for Adafruit Industries
#
# SPDX-License-Identifier: MIT

import numpy as np
from PIL import Image, ImageDraw

import adafruit_blinka_raspberry_pi5_piomatter as piomatter
# VChain 매퍼를 import 합니다. 이것이 올바른 함수입니다.
from adafruit_blinka_raspberry_pi5_piomatter.pixelmappers import VChain

# --- 하드웨어 구성에 맞게 이 부분을 설정합니다 ---
# 1. 기본 단위 설정
panel_width = 64        # 패널 한 개의 가로 픽셀
panel_height = 32       # 패널 한 개의 세로 픽셀
n_panels_in_lane = 4    # 한 레인(체인)에 직렬로 연결된 패널 수
n_lanes = 3             # 사용한 레인(체인)의 수 (세로 줄 수)
n_addr_lines = 4        # 64x32 패널의 표준 주소 라인 수

# 2. 전체 디스플레이 크기 계산
width = panel_width * n_panels_in_lane  # 전체 가로: 64 * 4 = 256
height = panel_height * n_lanes         # 전체 세로: 32 * 3 = 96
# --- 설정 끝 ---

# Pillow 라이브러리를 사용해 그림을 그릴 캔버스를 생성합니다.
canvas = Image.new('RGB', (width, height), (0, 0, 0))
draw = ImageDraw.Draw(canvas)

# ★★★★★ 진짜 최종 수정 부분 ★★★★★
# VChain 함수를 라이브러리가 요구하는 정확한 인자로 호출합니다.
pixelmap = VChain(
    width,              # 1. 전체 디스플레이의 가로 크기 (256)
    height,             # 2. 전체 디스플레이의 세로 크기 (96)
    n_addr_lines,       # 3. 패널의 주소 라인 수 (4)
    n_lanes,            # 4. 병렬로 사용되는 레인(채널)의 수 (3)
    n_panels_in_lane    # 5. 한 레인(채널)에 연결된 패널의 수 (4)
)

# Geometry와 PioMatter 객체 생성
geometry = piomatter.Geometry(width=width, height=height, n_addr_lines=n_addr_lines, n_planes=10, n_temporal_planes=4, map=pixelmap, n_lanes=n_lanes)
framebuffer = np.asarray(canvas) + 0  # 수정 가능한 복사본 생성
matrix = piomatter.PioMatter(colorspace=piomatter.Colorspace.RGB888Packed,
                             pinout=piomatter.Pinout.Active3,
                             framebuffer=framebuffer,
                             geometry=geometry)

# --- 이제 256x96 크기의 캔버스에 그림을 그립니다 ---
# 예시: 화면 전체에 그라데이션 만들기
for y in range(height):
    for x in range(width):
        r = int(x / width * 255)
        g = int(y / height * 255)
        b = 128
        draw.point((x, y), (r, g, b))

# 예시: 화면 중앙에 흰색 텍스트 쓰기
from PIL import ImageFont
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
except IOError:
    font = ImageFont.load_default()
draw.text((width/2, height/2), "256 x 96 OK!", font=font, anchor="mm", fill=(255, 255, 255))


# 수정한 캔버스 내용을 실제 디스플레이로 보냅니다.
framebuffer[:] = np.asarray(canvas)
matrix.show()

input("Press enter to exit")
