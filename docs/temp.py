import math

# 定義三個區塊
title_1 = [72, 619.49, 193.297, 608.742]
text_1 = [72, 599.431, 540.004, 488.048]
title_3 = [72, 480.013, 281.359, 469.265]

# 計算重心
def get_centroid(box):
    x1, y1, x2, y2 = box
    cx = (x1 + x2) / 2
    cy = (y1 + y2) / 2
    return (cx, cy)

# 計算兩點的歐幾里得距離
def distance(p1, p2):
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

centroid_title_1 = get_centroid(title_1)
centroid_text_1 = get_centroid(text_1)
centroid_title_3 = get_centroid(title_3)

# 計算距離
dist_text1_to_title1 = distance(centroid_text_1, centroid_title_1)
dist_title3_to_title1 = distance(centroid_title_3, centroid_title_1)

print("text_1 -> title_1 距離:", dist_text1_to_title1)
print("title_3 -> title_1 距離:", dist_title3_to_title1)