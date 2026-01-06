# find_pins.py
from src.pca9685_smbus import PCA9685, find_pca_bus
import time
import sys

def main():
    print("--- 腳位尋找工具 (Pin Finder) ---")
    print("這個程式會依序對 PCA9685 的 Channel 0 ~ 6 送出 PWM 訊號。")
    print("請觀察並記錄：")
    print("  Channel X 亮起時 -> 哪一輪轉動？ 往哪個方向？")
    print("------------------------------------------------")

    bus = find_pca_bus()
    if not bus:
        print("找不到 PCA9685")
        sys.exit(1)
        
    pca = PCA9685(bus)
    pca.set_frequency(200)
    
    # 先全停
    pca.stop_all()

    try:
        # 測試範圍：Channel 0 到 6 (通常你的接線都在這範圍)
        # 如果你的接線在更後面(例如 14, 15)，請自行修改 range(0, 16)
        # for channel in range(0, 7):
            channel = 1
            print(f"\n[測試中] 正在啟動 Channel {channel} ...")
            
            # 對該腳位送出 50% PWM，其他腳位全關
            pca.stop_all()
            pca.duty(channel, 0.5) 
            
            time.sleep(2) # 轉動 2 秒讓你觀察
            
            pca.stop_all()
            print(f"Channel {channel} 測試結束 (停止)")
            time.sleep(1)
            
    except KeyboardInterrupt:
        pass
    finally:
        pca.stop_all()
        print("\n--- 測試完成 ---")
        print("請根據剛才的觀察結果修改 config.py")

if __name__ == "__main__":
    main()