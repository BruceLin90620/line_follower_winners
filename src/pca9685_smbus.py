# src/pca9685_smbus.py
import time
from smbus2 import SMBus

class PCA9685:
    # Registers
    MODE1      = 0x00
    PRESCALE   = 0xFE
    LED0_ON_L  = 0x06

    def __init__(self, bus_num=7, address=0x40):
        print(f"PCA9685 Init: Opening Bus {bus_num} at address {hex(address)}")
        self.bus = SMBus(bus_num)
        self.address = address
        
        # 1. Reset
        self.write8(self.MODE1, 0x00)
        time.sleep(0.01)
        
        # 2. 先全停
        self.stop_all()

    def write8(self, reg, val):
        """
        寫入單一 Byte
        """
        try:
            self.bus.write_byte_data(self.address, reg, val & 0xFF)
        except Exception as e:
            print(f"I2C Error (write8): {e}")

    def read8(self, reg):
        try:
            return self.bus.read_byte_data(self.address, reg)
        except Exception as e:
            print(f"I2C Error (read8): {e}")
            return 0

    def set_pwm(self, ch, on, off):
        """
        【關鍵修改】
        改回跟 motor_test_l298n.py 一模一樣的寫法：
        分 4 次寫入，不使用 write_i2c_block_data。
        """
        base = self.LED0_ON_L + 4 * ch
        # ON LOW
        self.write8(base + 0, on & 0xFF)
        # ON HIGH
        self.write8(base + 1, (on >> 8) & 0xFF)
        # OFF LOW
        self.write8(base + 2, off & 0xFF)
        # OFF HIGH
        self.write8(base + 3, (off >> 8) & 0xFF)

    def duty(self, ch, x):
        """
        設定 Duty Cycle (0.0 ~ 1.0)
        """
        x = max(0.0, min(1.0, x))
        if x <= 0.0:
            self.set_pwm(ch, 0, 0)
        elif x >= 1.0:
            # Full on: use off=4096 (Bit 4 of LED_ON_H set)
            # 這是測試程式驗證過可行的寫法
            self.set_pwm(ch, 4096, 0)
        else:
            off = int(x * 4095)
            self.set_pwm(ch, 0, off)

    def dig(self, ch, high: bool):
        self.duty(ch, 1.0 if high else 0.0)

    def set_frequency(self, freq_hz):
        prescale = int(round(25000000.0 / (4096.0 * freq_hz)) - 1)
        old = self.read8(self.MODE1)
        sleep = (old & 0x7F) | 0x10
        self.write8(self.MODE1, sleep)
        self.write8(self.PRESCALE, prescale)
        self.write8(self.MODE1, old)
        time.sleep(0.005)
        self.write8(self.MODE1, old | 0x80)

    def stop_all(self):
        for ch in range(16):
            self.duty(ch, 0.0)

# Helper function for main.py
def find_pca_bus(address=0x40):
    return 7