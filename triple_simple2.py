#!/usr/bin/python3
# SPDX-FileCopyrightText: 2025 Tim Cocks for Adafruit Industries
#
# SPDX-License-Identifier: MIT

import numpy as np
from PIL import Image, ImageDraw

import adafruit_blinka_raspberry_pi5_piomatter as piomatter
# 'simple_multilane_mapper' 대신 'chained_multilane_mapper'를 import 합니다.
from adafruit_blinka_raspberry_pi5_piomatter.pixelmappers import chained_multilane_mapper

# --- 하드웨어 구성에 맞게 이 부분을 수정합니다 ---
panel_width = 64     # 패널 한 개의 가로 픽셀
panel_height = 32    # 패널 한 개의 세로 픽셀
n_panels_x = 4       # 한 채널에 가로로 연결된 패널 수
n_panels_y = 3       # 사용한 채널(lane)의 수 (세로 줄 수)
n_addr_lines = 4     # 64x32 패널은 4가 표준입니다.

# 전체 디스플레이 크기를 자동으로 계산합니다.
width = panel_width * n_panels_x     # 64 * 4 = 256
height = panel_height * n_panels_y   # 32 * 3 = 96
n_lanes = n_panels_y                 # 채널 수는 세로 패널 수와 같습니다.
# --- 설정 끝 ---

# Pillow 라이브러리를 사용해 그림을 그릴 캔버스를 생성합니다.
canvas = Image.new('RGB', (width, height), (0, 0, 0))
draw = ImageDraw.Draw(canvas)

# 수정된 부분: chained_multilane_mapper를 사용합니다.
pixelmap = chained_multilane_mapper(panel_width, panel_height, n_panels_x, n_panels_y, n_addr_lines)

# Geometry와 PioMatter 객체 생성은 거의 동일하지만, 변수들을 올바르게 전달합니다.
geometry = piomatter.Geometry(width=width, height=height, n_addr_lines=n_addr_lines, n_planes=10, n_temporal_planes=4, map=pixelmap, n_lanes=n_lanes)
framebuffer = np.asarray(canvas) + 0  # 수정 가능한 복사본 생성
matrix = piomatter.PioMatter(colorspace=piomatter.Colorspace.RGB888Packed,
                             pinout=piomatter.Pinout.Active3,
                             framebuffer=framebuffer,
                             geometry=geometry)

# --- 이제 256x96 크기의 캔버스에 그림을 그립니다 ---
# 예시: 화면 중앙에 큰 녹색 사각형 그리기
draw.rectangle((10, 10, width - 10, height - 10), fill=(0, 128, 0), outline=(0, 255, 0))

# 예시: 화면 좌측 상단에 작은 빨간색 원 그리기
draw.ellipse((20, 20, 60, 60), fill=(200, 0, 0))

# 예시: 화면 우측 하단에 파란색 글씨 쓰기 (글꼴 파일이 필요할 수 있습니다)
# from PIL import ImageFont
# font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
# draw.text((150, 60), "Hello!", font=font, fill=(0, 0, 255))

# 수정한 캔버스 내용을 실제 디스플레이로 보냅니다.
framebuffer[:] = np.asarray(canvas)
matrix.show()

input("Press enter to exit")
