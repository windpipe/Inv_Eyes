#!/usr/bin/python3
# SPDX-FileCopyrightText: 2025 Tim Cocks for Adafruit Industries
#
# SPDX-License-Identifier: MIT

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import adafruit_blinka_raspberry_pi5_piomatter as piomatter
# Your library only has this one mapper, so we will use it.
from adafruit_blinka_raspberry_pi5_piomatter.pixelmappers import simple_multilane_mapper

# --- 1. Define physical hardware layout ---
panel_width = 64
panel_height = 32
panels_per_chain = 4
num_physical_chains = 3
n_addr_lines = 4

# --- 2. Calculate true display dimensions ---
width = panel_width * panels_per_chain    # 64 * 4 = 256
height = panel_height * num_physical_chains # 32 * 3 = 96

# --- 3. The Workaround: "Trick" the mapper ---
# We calculate the number of "lanes" the simple_multilane_mapper EXPECTS.
# It assumes lane_height is 16 (2**4), so we need 6 "virtual" lanes to make a 96px total height.
n_lanes_for_mapper = height // (1 << n_addr_lines)  # 96 // 16 = 6

# --- 4. Pillow 캔버스 생성 ---
canvas = Image.new('RGB', (width, height), (0, 0, 0))
draw = ImageDraw.Draw(canvas)

# ★★★★★ 이 부분이 핵심입니다 ★★★★★
# We pass the "fake" number of lanes (6) to the mapper so its internal check passes.
pixelmap = simple_multilane_mapper(width, height, n_addr_lines, n_lanes_for_mapper)


# --- 5. PioMatter 객체 설정 ---
# IMPORTANT: We must also tell Geometry and PioMatter about the "fake" number of lanes.
# The library will try to drive 6 lanes, but since only 3 are physically wired,
# the data for the other 3 will go nowhere, which is harmless.
geometry = piomatter.Geometry(width=width, height=height, n_addr_lines=n_addr_lines, n_planes=10, n_temporal_planes=4, map=pixelmap, n_lanes=n_lanes_for_mapper)
framebuffer = np.asarray(canvas) + 0
matrix = piomatter.PioMatter(colorspace=piomatter.Colorspace.RGB888Packed,
                             pinout=piomatter.Pinout.Active3,
                             framebuffer=framebuffer,
                             geometry=geometry)

# --- 6. 디스플레이에 내용 그리기 ---
draw.rectangle((0, 0, width-1, height-1), outline=(255,0,0))
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
except IOError:
    font = ImageFont.load_default()
draw.text((width/2, height/2), "WORKAROUND SUCCESS!\n256x96", font=font, anchor="mm", fill=(0, 255, 0), align="center")


# --- 7. 화면에 출력 ---
framebuffer[:] = np.asarray(canvas)
matrix.show()

input("Press enter to exit")
