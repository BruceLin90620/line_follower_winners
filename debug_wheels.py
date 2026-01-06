# debug_wheels.py
from src.pca9685_smbus import PCA9685, find_pca_bus
from src.motors_l298n import MotorDriver
import time
import sys

def main():
    print("--- 終極輪子除錯模式 ---")
    print("請將車子架高 (輪子離地)！")
    print("這程式會一顆一顆輪子測試，請用眼睛觀察輪子轉動方向。")
    print("-------------------------")

    bus = find_pca_bus()
    if not bus:
        print("找不到 PCA9685")
        sys.exit(1)
        
    pca = PCA9685(bus)
    pca.set_frequency(200)
    motors = MotorDriver(pca)

    try:
        # --- 測試 1: 左輪 ---
        print("\n[測試 A] 左輪 - 前進 (Left Forward)")
        print("觀察：左輪應該要向前轉，右輪不動。")
        motors.left.set_target(0.6)
        motors.right.set_target(0) # 右輪鎖死
        time.sleep(2)
        motors.stop()
        
        input("按 Enter 繼續測試右輪...")

        # --- 測試 2: 右輪 ---
        print("\n[測試 B] 右輪 - 前進 (Right Forward)")
        print("觀察：右輪應該要向前轉，左輪不動。")
        motors.left.set_target(0) # 左輪鎖死
        motors.right.set_target(0.6) 
        time.sleep(2)
        motors.stop()

        input("按 Enter 繼續測試反轉...")

        # --- 測試 3: 左輪反轉 ---
        print("\n[測試 C] 左輪 - 後退 (Left Backward)")
        motors.left.set_target(-0.6)
        motors.right.set_target(0)
        time.sleep(2)
        motors.stop()

        # --- 測試 4: 右輪反轉 ---
        print("\n[測試 D] 右輪 - 後退 (Right Backward)")
        motors.left.set_target(0)
        motors.right.set_target(-0.6)
        time.sleep(2)
        motors.stop()
        
    except KeyboardInterrupt:
        print("停止")
    finally:
        motors.stop()
        print("測試結束")

if __name__ == "__main__":
    main()