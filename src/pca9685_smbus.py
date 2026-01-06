# src/pca9685_smbus.py
import time
from smbus2 import SMBus


class PCA9685:
    """
    PCA9685：16 通道 PWM 控制器（I2C 介面）
    - 使用 smbus2 操作 I2C
    - 提供 set_pwm / duty / dig / set_frequency / stop_all 等常用功能
    """

    # ===== PCA9685 重要暫存器位址 =====
    MODE1 = 0x00 # MODE1 暫存器（位址 0x00）
    PRESCALE = 0xFE # PRESCALE 暫存器（位址 0xFE）
    LED0_ON_L = 0x06  # PWM 通道 0 的 ON_L 起始位址（每個通道占 4 bytes）

    def __init__(self, bus_num: int = 7, address: int = 0x40):
        """
        初始化 PCA9685
        :param bus_num: I2C bus 編號（Jetson / Linux 可能是 1、7... 依實機而定）
        :param address: PCA9685 I2C 位址（常見為 0x40）
        """
        self.bus_num = bus_num
        self.address = address

        print(f"PCA9685 Init: Opening Bus {bus_num} at address {hex(address)}")
        self.bus = SMBus(bus_num)

        # 1) Reset：寫 MODE1=0x00，回到一般模式（也等同關掉 sleep）
        self.write8(self.MODE1, 0x00)
        time.sleep(0.01)

        # 2) 先全停（安全起見，避免一初始化就輸出 PWM）
        self.stop_all()

    # ===== 基本 I2C 讀寫 =====
    def write8(self, reg: int, val: int) -> None:
        """
        寫入單一 byte 到指定暫存器
        :param reg: 暫存器位址
        :param val: 要寫入的值（只取低 8 bits）
        """
        try:
            self.bus.write_byte_data(self.address, reg, val & 0xFF) # I2C 寫入：將 val 取低 8 位元後，寫入指定裝置的暫存器 reg。
        except Exception as e:
            print(f"I2C Error (write8): {e}")

    def read8(self, reg: int) -> int:
        """
        讀取指定暫存器的單一 byte
        :param reg: 暫存器位址
        :return: 讀到的值；若失敗回傳 0
        """
        try:
            return self.bus.read_byte_data(self.address, reg)
        except Exception as e:
            print(f"I2C Error (read8): {e}")
            return 0

    # ===== PWM 設定 =====
    def _channel_base_reg(self, ch: int) -> int:
        """
        計算某個通道對應的起始暫存器位址
        每個通道佔用 4 bytes：ON_L, ON_H, OFF_L, OFF_H
        """
        return self.LED0_ON_L + 4 * ch

    def set_pwm(self, ch: int, on: int, off: int) -> None:
        """
        設定單一通道 PWM 的 ON / OFF 計數值（0~4096）
        【保留原本關鍵行為】：
        - 分 4 次 write8 寫入（不使用 write_i2c_block_data）
        """
        base = self._channel_base_reg(ch)

        # ON LOW / HIGH
        self.write8(base + 0, on & 0xFF)
        self.write8(base + 1, (on >> 8) & 0xFF)

        # OFF LOW / HIGH
        self.write8(base + 2, off & 0xFF)
        self.write8(base + 3, (off >> 8) & 0xFF)

    def duty(self, ch: int, x: float) -> None:
        """
        設定 Duty Cycle（0.0 ~ 1.0）
        :param ch: 通道 0~15
        :param x: duty 比例（會自動 clamp 到 0.0~1.0）
        """
        # clamp，避免輸入超出範圍
        x = max(0.0, min(1.0, x))

        if x <= 0.0:
            # 全關：on=0 off=0
            self.set_pwm(ch, 0, 0)

        elif x >= 1.0:
            # 全開（Full on）
            self.set_pwm(ch, 4096, 0)

        else:
            # 一般 PWM：on=0，off= duty*4095
            off = int(x * 4095)
            self.set_pwm(ch, 0, off)

    def dig(self, ch: int, high: bool) -> None:
        """
        將某通道當作數位輸出使用：True=高（等同 100% duty），False=低（0% duty）
        """
        self.duty(ch, 1.0 if high else 0.0)

    # ===== 頻率設定 =====
    def set_frequency(self, freq_hz: float) -> None:
        """
        設定 PCA9685 PWM 頻率（Hz）
        - PCA9685 內部時鐘 25MHz（標準值）
        - prescale = round(25e6 / (4096 * freq)) - 1
        """
        prescale = int(round(25000000.0 / (4096.0 * freq_hz)) - 1)

        # 先把晶片切到 sleep 才能安全寫 prescale
        old_mode1 = self.read8(self.MODE1)
        mode1_sleep = (old_mode1 & 0x7F) | 0x10  # 0x10 = SLEEP bit

        self.write8(self.MODE1, mode1_sleep)
        self.write8(self.PRESCALE, prescale)

        # 還原 MODE1
        self.write8(self.MODE1, old_mode1)
        time.sleep(0.005)

        # 重啟（RESTART bit）
        self.write8(self.MODE1, old_mode1 | 0x80)

    # ===== 安全停車 =====
    def stop_all(self) -> None:
        """
        將 16 個通道全部設為 0% duty（全停）
        """
        for ch in range(16):
            self.duty(ch, 0.0)