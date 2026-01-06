# src/vision_line.py
import cv2
import numpy as np
from .config import *


class Vision:
    """
    循跡視覺處理：
    - 從影像中取 ROI（通常是下方區域）
    - 二值化分割線條
    - 形態學去噪
    - 用 moments 計算線條質心（centroid）
    - 輸出 error（偏差）與 confidence（可信度）
    """

    def process(self, frame):
        """
        影像處理主流程

        Args:
            frame (image): BGR 影像（OpenCV 讀到的原圖）

        Returns:
            error (float): -1.0（偏左）~ 1.0（偏右），0.0 表示線在畫面中央
            confidence (float): 0.0 ~ 1.0，以白色像素面積比例估計偵測可信度
            mask (image): 二值化遮罩圖（0/255）
            debug_frame (image): 附帶標示中心線與質心的可視化影像（ROI 範圍）
        """
        h, w = frame.shape[:2]

        # ===== 1) ROI 選取 =====
        # 只取畫面某個垂直比例範圍（例如下方），降低干擾並加速運算
        y_start = int(h * ROI_Y_START_RATIO)
        y_end = int(h * ROI_Y_END_RATIO)
        roi = frame[y_start:y_end, 0:w]

        # ===== 2) 前處理：灰階 + 高斯模糊 =====
        # 灰階：降低通道
        # 模糊：降低雜訊，讓 threshold 更穩
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)

        # ===== 3) 二值化（Thresholding）=====
        # INVERT_THRESH=True：使用 THRESH_BINARY_INV（黑白反轉）
        # INVERT_THRESH=False：使用 THRESH_BINARY
        thresh_type = cv2.THRESH_BINARY_INV if INVERT_THRESH else cv2.THRESH_BINARY
        _, mask = cv2.threshold(blur, THRESH_VAL, 255, thresh_type)

        # ===== 4) 形態學去噪（Morphology）=====
        # OPEN：先 erode 再 dilate，去除小白點雜訊
        # CLOSE：先 dilate 再 erode，填補小黑洞
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        # ===== 5) 計算質心（Centroid）與輸出 error / confidence =====
        # moments 可以得到白色區域的面積與一階矩，用於算質心
        M = cv2.moments(mask)

        if M["m00"] > 0:
            # m00：面積（像素值加總），對二值圖而言近似白色面積 * 255
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])

            # error 正規化到 [-1, 1]
            # cx < w/2 => 負（偏左）
            # cx > w/2 => 正（偏右）
            error = (cx - (w / 2)) / (w / 2)

            # confidence：白色面積比例（0~1）
            # M["m00"] 大約是（白色像素數 * 255）
            confidence = M["m00"] / (255 * mask.size)
        else:
            # 完全沒偵測到白色區域：回報 error=0 並將 confidence=0
            cx, cy = w // 2, 0
            error = 0.0
            confidence = 0.0

        # ===== 6) Debug 可視化 =====
        # 在 ROI 上畫出中心線（綠）與質心點（紅），並顯示 error/conf
        debug = roi.copy()

        # 原本程式寫法：(... >= 0 or True) 永遠為 True
        # 這裡保留不改動，仍然每次都畫 debug（功能保持不變）
        if cv2.getWindowProperty("Debug", cv2.WND_PROP_VISIBLE) >= 0 or True:
            # 畫 ROI 中心線（綠色）
            cv2.line(
                debug,
                (w // 2, 0),
                (w // 2, debug.shape[0]),
                (0, 255, 0),
                1,
            )

            # 若有偵測到質心就畫出來並標示文字
            if M["m00"] > 0:
                cv2.circle(debug, (cx, cy), 5, (0, 0, 255), -1)
                cv2.putText(
                    debug,
                    f"Err: {error:.2f}",
                    (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 0, 255),
                    1,
                )
                cv2.putText(
                    debug,
                    f"Conf: {confidence:.2f}",
                    (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 0, 255),
                    1,
                )

        return error, confidence, mask, debug


def _run_vision_test():
    """
    測試模式：用 USB Camera + Vision
    - 用於調整 config.py 的 THRESH_VAL / ROI 相關參數
    - 按 q 離開
    """
    from .camera_usb import Camera

    print("--- Testing Vision Algorithm ---")
    print("Use this mode to tune THRESH_VAL in config.py")

    cam = Camera()
    vision = Vision()

    try:
        while True:
            ret, frame = cam.read()
            if not ret:
                break

            err, conf, mask, debug = vision.process(frame)

            # 在 Terminal 顯示即時數值（同你原本做法）
            print(f"\rError: {err:.2f} | Conf: {conf:.2f}", end="")

            cv2.imshow("Mask (Should be white line on black)", mask)
            cv2.imshow("Debug (Green Line = Center)", debug)

            if cv2.waitKey(1) == ord("q"):
                break

    except KeyboardInterrupt:
        pass

    finally:
        cam.close()
        cv2.destroyAllWindows()
        print("\nDone.")


if __name__ == "__main__":
    # 測試指令：python3 -m src.vision_line
    _run_vision_test()
