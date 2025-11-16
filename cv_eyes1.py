import cv2
import numpy as np
import math

# 캔버스 크기
H, W = 256, 256

# 큰 검은 원 설정
big_center = (120, 130)
big_radius = 110

# 안쪽 작은 검은 원 (막대 중심) 설정
sun_center = (170, 80)
sun_radius = 22

# 흰 막대들 (8개 방사형) 설정
num_rays = 8
inner_r = sun_radius + 4    # 막대가 시작하는 반지름
outer_r = sun_radius + 24   # 막대가 끝나는 반지름
thickness = 7

# 애니메이션 루프
angle_offset = 0
bg_is_white = True  # 배경색 토글 (True: 흰색, False: 검은색)

while True:
    # 배경색 설정
    bg_color = 255 if bg_is_white else 0
    
    # 매 프레임마다 새로운 캔버스 생성
    img = np.full((H, W, 3), bg_color, np.uint8)
    
    # 큰 검은 원 그리기
    cv2.circle(img, big_center, big_radius, (20, 20, 20), -1)
    
    # 안쪽 작은 검은 원 그리기
    cv2.circle(img, sun_center, sun_radius, (20, 20, 20), -1)
    
    # 회전하는 흰 막대들 그리기
    for i in range(num_rays):
        angle = 2 * math.pi * i / num_rays + angle_offset
        
        x1 = int(sun_center[0] + inner_r * math.cos(angle))
        y1 = int(sun_center[1] + inner_r * math.sin(angle))
        x2 = int(sun_center[0] + outer_r * math.cos(angle))
        y2 = int(sun_center[1] + outer_r * math.sin(angle))
        
        cv2.line(img, (x1, y1), (x2, y2), (255, 255, 255), thickness, cv2.LINE_AA)
    
    # 화면에 표시
    cv2.imshow("Animated Icon", img)
    
    # 각도 업데이트 (회전 속도)
    angle_offset += 0.05
    
    # 키 입력 처리
    key = cv2.waitKey(30)  # 30ms 대기 (약 33 FPS)
    if key == 27:  # ESC 키를 누르면 종료
        break
    elif key == 32:  # 스페이스바를 누르면 배경색 토글
        bg_is_white = not bg_is_white

cv2.destroyAllWindows()

# 마지막 프레임 저장
cv2.imwrite("brightness_icon_opencv.png", img)
