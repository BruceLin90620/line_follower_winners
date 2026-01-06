# src/main.py
import cv2
import time
import traceback

# 以 module 方式執行（python3 -m src.main）時的相對匯入
from .config import *
from .pca9685_smbus import PCA9685
from .motors_l298n import MotorDriver
from .camera_usb import Camera
from .vision_line import Vision
from .controller_pd import PDController


def main():
    """
    主程式：循跡車控制迴圈
    流程概念：
      1) 初始化硬體（PCA9685 / 馬達）
      2) 初始化感知（Camera / Vision）
      3) 初始化控制（PD）
      4) 以固定 CONTROL_HZ 迴圈：
         - 讀影像 → Vision 算 error/conf
         - conf 太低：停車（安全機制）
         - 否則：PD 產生左右輪命令 → 馬達輸出
    """
    print("Initializing Line Follower...")

    # ===== 1) 初始化 PCA9685（I2C PWM 控制器）=====
    # 使用 config.py：I2C_BUS / PCA_ADDR / PCA_FREQ
    pca = PCA9685(I2C_BUS, PCA_ADDR)
    pca.set_frequency(PCA_FREQ)

    # ===== 2) 初始化馬達驅動（L298N + PCA9685）=====
    motors = MotorDriver(pca)

    # ===== 3) 初始化攝影機 =====
    cam = None
    try:
        cam = Camera()
    except RuntimeError as e:
        print(e)
        return

    # ===== 4) 初始化視覺與控制器 =====
    vision = Vision()
    controller = PDController()

    print("System Ready. Press 'q' in window or Ctrl+C to stop.")

    # ===== 5) 迴圈節流：以 CONTROL_HZ 控制更新頻率 =====
    # dt：每次迴圈最短間隔
    dt = 1.0 / CONTROL_HZ
    last_time = time.time()

    try:
        while True:
            # --- A) 迴圈 timing（節流到 CONTROL_HZ）---
            now = time.time()
            if now - last_time < dt:
                # 還沒到下一個週期，稍微 sleep 讓出 CPU
                time.sleep(0.001)
                continue
            last_time = now

            # --- B) 感知：讀影像 + Vision 算誤差/可信度 ---
            ret, frame = cam.read()
            if not ret:
                print("Failed to capture image")
                break

            error, conf, mask, debug = vision.process(frame)

            # --- C) 安全 + 控制 ---
            # 若 conf 太低，視為「找不到線」，立刻停車
            if conf < MIN_CONFIDENCE:
                print(f"Lost Line! (Conf: {conf:.2f}) - STOP")
                motors.stop()
            else:
                # PD 控制器輸出左右輪命令
                left_cmd, right_cmd = controller.step(error)
                motors.set(left_cmd, right_cmd)

                # 監看用輸出（保持你原本的 print 行為）
                print(f"Err: {error:.2f} | L: {left_cmd:.2f} | R: {right_cmd:.2f}")

            # --- D) 可視化（目前保留註解，功能不變）---
            # cv2.imshow("Debug", debug)
            # cv2.imshow("Mask", mask)

            # 注意：即使沒有 imshow，waitKey 仍可用來接收鍵盤（但視窗沒開時意義較小）
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    except KeyboardInterrupt:
        print("\nCtrl+C detected.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        traceback.print_exc()
    finally:
        # ===== 6) 清理資源（確保安全停車）=====
        print("Cleaning up...")

        # 停止馬達輸出（使用你 MotorDriver 的 stop）
        motors.stop()

        # PCA9685 全通道 duty=0（更保險）
        pca.stop_all()

        # 關閉攝影機
        if cam is not None:
            cam.close()

        # 關閉 OpenCV 視窗
        cv2.destroyAllWindows()

        print("Stopped safely.")


if __name__ == "__main__":
    main()
