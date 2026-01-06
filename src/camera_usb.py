# src/camera_usb.py
import cv2
from .config import *

class Camera:
    def __init__(self):
        self.cap = cv2.VideoCapture(CAM_INDEX, cv2.CAP_V4L2)
        if not self.cap.isOpened():
            raise RuntimeError(f"Could not open camera index {CAM_INDEX}")
            
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS, CAM_FPS)
        
    def read(self):
        return self.cap.read()
        
    def close(self):
        if self.cap.isOpened():
            self.cap.release()

if __name__ == "__main__":
    # 測試指令：python3 -m src.camera_usb
    print("--- Testing Camera ---")
    print("Press 'q' to exit.")
    
    try:
        cam = Camera()
        while True:
            ret, frame = cam.read()
            if ret:
                cv2.imshow("Camera Test", frame)
            else:
                print("Frame error")
                break
                
            if cv2.waitKey(1) == ord('q'):
                break
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'cam' in locals():
            cam.close()
        cv2.destroyAllWindows()
