from rplidar import RPLidar
import threading
import time
import math

class LidarSensor:
    def __init__(self, port='/dev/ttyUSB0', baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.lidar = None
        self.running = False
        self.lock = threading.Lock()
        
        # 儲存最新的障礙物資訊
        # 格式: {角度: 距離mm, ...}
        self.scan_data = {}
        
        # 預設前方的最小距離 (mm)
        self.min_front_dist = 9999.0

    def start(self):
        """啟動 LiDAR 掃描執行緒"""
        try:
            self.lidar = RPLidar(self.port, baudrate=self.baudrate)
            self.running = True
            # 開啟一個執行緒在背景跑 update()
            self.thread = threading.Thread(target=self._update, daemon=True)
            self.thread.start()
            print(f"[LiDAR] Connected to {self.port}")
        except Exception as e:
            print(f"[LiDAR] Connection Failed: {e}")

    def stop(self):
        self.running = False
        if self.lidar:
            self.lidar.stop()
            self.lidar.disconnect()
            time.sleep(1)

    def _update(self):
        """背景迴圈：不斷讀取雷達數據"""
        while self.running:
            try:
                # iter_scans 會回傳一整圈的數據
                for scan in self.lidar.iter_scans():
                    if not self.running: break
                    
                    # scan 格式: [(quality, angle, distance), ...]
                    # 我們要過濾出「正前方」的數據
                    # 假設 LiDAR 線朝後裝，0度通常是車頭方向 (視安裝而定，可能需調整)
                    
                    temp_min_dist = 9999.0
                    
                    for (_, angle, dist) in scan:
                        if dist <= 0: continue # 過濾無效數據
                        
                        # 定義「前方」的範圍：例如 0度 ± 30度
                        # RPLidar 的角度是 0~360
                        # 0度左右 = (angle < 30) or (angle > 330)
                        if (angle < 30) or (angle > 330):
                            if dist < temp_min_dist:
                                temp_min_dist = dist
                    
                    # 更新共用變數 (加鎖保護)
                    with self.lock:
                        self.min_front_dist = temp_min_dist
                        
            except Exception as e:
                print(f"[LiDAR] Error: {e}")
                # 嘗試重連
                try:
                    self.lidar.stop()
                    self.lidar.disconnect()
                    time.sleep(1)
                    self.lidar.connect()
                except:
                    pass

    def get_front_distance(self):
        """主程式呼叫這個函式，獲取當前前方最近距離"""
        with self.lock:
            return self.min_front_dist

if __name__ == "__main__":
    # 測試程式
    lidar = LidarSensor()
    lidar.start()
    try:
        while True:
            dist = lidar.get_front_distance()
            print(f"Front Distance: {dist:.1f} mm")
            time.sleep(0.1)
    except KeyboardInterrupt:
        lidar.stop()