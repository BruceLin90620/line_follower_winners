# src/camera_usb.py
import cv2
from .config import *


class Camera:
    """
    USB 攝影機封裝（OpenCV + V4L2）
    - 使用 config.py 的參數：
      CAM_INDEX, CAM_WIDTH, CAM_HEIGHT, CAM_FPS
    """

    def __init__(self):
        # 使用 V4L2 後端開啟指定的攝影機 index（例如 0、1...）
        self.cap = cv2.VideoCapture(CAM_INDEX, cv2.CAP_V4L2)

        # 確認攝影機是否成功打開
        if not self.cap.isOpened():
            raise RuntimeError(f"Could not open camera index {CAM_INDEX}")

        # 設定影像寬高與 FPS（注意：部分攝影機可能不完全支援，實際值需再 query）
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS, CAM_FPS)

    def read(self):
        """
        讀取一張影像
        :return: (ret, frame)
          - ret: bool，是否成功
          - frame: 影像 ndarray（BGR）
        """
        return self.cap.read()

    def close(self):
        """
        釋放攝影機資源
        """
        if self.cap.isOpened():
            self.cap.release()


def _run_camera_test():
    """
    測試模式：開啟攝影機並顯示畫面
    - 按 'q' 離開
    """
    print("--- Testing Camera ---")
    print("Press 'q' to exit.")

    cam = None
    try:
        cam = Camera()

        while True:
            ret, frame = cam.read()

            # 讀不到影像時直接中止
            if not ret:
                print("Frame error")
                break

            # 顯示畫面
            cv2.imshow("Camera Test", frame)

            # 每次等待 1ms，按下 'q' 離開
            if cv2.waitKey(1) == ord('q'):
                break

    except Exception as e:
        print(f"Error: {e}")

    finally:
        # 確保資源釋放
        if cam is not None:
            cam.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    # 測試指令：python3 -m src.camera_usb
    _run_camera_test()
