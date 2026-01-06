# src/vision_line.py
import cv2
import numpy as np
from .config import *

class Vision:
    def process(self, frame):
        """
        Returns:
            error (float): -1.0 (left) to 1.0 (right), 0.0 is center
            confidence (float): 0.0 to 1.0 (ratio of white pixels)
            mask (image): Binary image
            debug_frame (image): Visualization
        """
        h, w = frame.shape[:2]
        
        # 1. ROI Selection
        y_start = int(h * ROI_Y_START_RATIO)
        y_end = int(h * ROI_Y_END_RATIO)
        roi = frame[y_start:y_end, 0:w]
        
        # 2. Preprocessing
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # 3. Thresholding
        thresh_type = cv2.THRESH_BINARY_INV if INVERT_THRESH else cv2.THRESH_BINARY
        _, mask = cv2.threshold(blur, THRESH_VAL, 255, thresh_type)
        
        # 4. Morphology (Noise reduction)
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        # 5. Centroid Calculation
        M = cv2.moments(mask)
        if M['m00'] > 0:
            cx = int(M['m10'] / M['m00'])
            cy = int(M['m01'] / M['m00'])
            
            # Normalize error to [-1, 1]
            # Center is w/2. 
            # If cx is small (left), error is negative.
            # If cx is large (right), error is positive.
            error = (cx - (w / 2)) / (w / 2)
            
            # Confidence: Area of white pixels / Total area
            confidence = M['m00'] / (255 * mask.size)
        else:
            cx, cy = w // 2, 0
            error = 0.0
            confidence = 0.0

        # 6. Debug Visualization
        debug = roi.copy()
        if cv2.getWindowProperty('Debug', cv2.WND_PROP_VISIBLE) >= 0 or True:
            # Draw center line
            cv2.line(debug, (w//2, 0), (w//2, debug.shape[0]), (0, 255, 0), 1)
            # Draw centroid
            if M['m00'] > 0:
                cv2.circle(debug, (cx, cy), 5, (0, 0, 255), -1)
                cv2.putText(debug, f"Err: {error:.2f}", (10, 20), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
                cv2.putText(debug, f"Conf: {confidence:.2f}", (10, 40), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

        return error, confidence, mask, debug

if __name__ == "__main__":
    # 測試指令：python3 -m src.vision_line
    from .camera_usb import Camera
    import time
    
    print("--- Testing Vision Algorithm ---")
    print("Use this mode to tune THRESH_VAL in config.py")
    
    cam = Camera()
    vision = Vision()
    
    try:
        while True:
            ret, frame = cam.read()
            if not ret: break
            
            err, conf, mask, debug = vision.process(frame)
            
            # 顯示資訊在 Terminal
            print(f"\rError: {err:.2f} | Conf: {conf:.2f}", end="")
            
            cv2.imshow("Mask (Should be white line on black)", mask)
            cv2.imshow("Debug (Green Line = Center)", debug)
            
            if cv2.waitKey(1) == ord('q'):
                break
    except KeyboardInterrupt:
        pass
    finally:
        cam.close()
        cv2.destroyAllWindows()
        print("\nDone.")
        