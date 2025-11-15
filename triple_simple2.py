#!/usr/bin/python3
# SPDX-FileCopyrightText: 2025 Tim Cocks for Adafruit Industries
#
# SPDX-License-Identifier: MIT

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import adafruit_blinka_raspberry_pi5_piomatter as piomatter
# 더 이상 simple_multilane_mapper는 import하지 않습니다.

# ★★★★★ 이 부분이 핵심입니다 ★★★★★
# 우리만의 커스텀 매퍼 함수를 정의합니다.
def my_serpentine_mapper(width, height, n_addr_lines, n_lanes):
    """
    홀수번째 주소 라인(addr)의 픽셀 순서를 뒤집어주는
    서펜타인(Z-Stripe) 레이아웃을 위한 커스텀 매퍼입니다.
    """
    n_addr = 1 << n_addr_lines
    
    m = []
    # 패널의 각 '주소 라인'을 순회합니다. (세로 방향)
    for addr in range(n_addr):
        
        # 기본적으로 x좌표는 왼쪽에서 오른쪽으로 순회합니다.
        x_coords = range(width)
        
        # 만약 '주소 라인'이 홀수번째라면 (1, 3, 5, ...),
        # x좌표 순서를 오른쪽에서 왼쪽으로 뒤집습니다.
        if addr % 2 != 0:
            x_coords = reversed(range(width))

        # 계산된 순서대로 x좌표를 순회합니다.
        for x in x_coords:
            # 각 레인(채널)을 순회합니다.
            for lane in range(n_lanes):
                # 실제 y좌표를 계산합니다.
                y = addr + lane * n_addr
                
                # 계산된 y좌표가 실제 디스플레이 높이를 벗어나지 않는지 확인합니다.
                # (저희가 6개의 가상 레인을 사용하기 때문에 이 확인이 필요합니다)
                if y < height:
                    framebuffer_index = x + width * y
                    m.append(framebuffer_index)
    return m


# --- 1. Define physical hardware layout ---
panel_width = 64
panel_height = 32
panels_per_chain = 4
num_physical_chains = 3
n_addr_lines = 4

# --- 2. Calculate true display dimensions ---
width = panel_width * panels_per_chain    # 256
height = panel_height * num_physical_chains # 96

# --- 3. The Workaround: Calculate "virtual lanes" for the library ---
n_lanes_for_mapper = height // (1 << n_addr_lines)  # 96 // 16 = 6

# --- 4. Pillow 캔버스 생성 ---
canvas = Image.new('RGB', (width, height), (0, 0, 0))
draw = ImageDraw.Draw(canvas)

# --- 5. 새로 만든 커스텀 매퍼를 사용합니다 ---
pixelmap = my_serpentine_mapper(width, height, n_addr_lines, n_lanes_for_mapper)


# --- 6. PioMatter 객체 설정 ---
geometry = piomatter.Geometry(width=width, height=height, n_addr_lines=n_addr_lines, n_planes=10, n_temporal_planes=4, map=pixelmap, n_lanes=n_lanes_for_mapper)
framebuffer = np.asarray(canvas) + 0
matrix = piomatter.PioMatter(colorspace=piomatter.Colorspace.RGB888Packed,
                             pinout=piomatter.Pinout.Active3,
                             framebuffer=framebuffer,
                             geometry=geometry)

# --- 7. 디스플레이에 내용 그리기 ---
draw.rectangle((0, 0, width-1, height-1), outline=(255,0,255), width=2)
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
except IOError:
    font = ImageFont.load_default()
draw.text((width/2, height/2), "ROTATION FIXED!", font=font, anchor="mm", fill=(0, 255, 255), align="center")


# --- 8. 화면에 출력 ---
framebuffer[:] = np.asarray(canvas)
matrix.show()

input("Press enter to exit")
