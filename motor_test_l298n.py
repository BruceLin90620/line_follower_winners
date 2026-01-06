import time
from smbus2 import SMBus

# ====== 你要改這裡：I2C bus 編號 ======
BUS = 7          # 例如 /dev/i2c-7 就填 7
ADDR = 0x40      # PCA9685 預設位址

# ====== L298N 對 PCA9685 channel 對應（照你接線調整）=====
# CH0->ENA, CH1->IN1, CH2->IN2, CH3->ENB, CH4->IN3, CH5->IN4
ENA, IN1, IN2 = 0, 1, 2
ENB, IN3, IN4 = 3, 4, 5

# PCA9685 registers
MODE1      = 0x00
PRESCALE   = 0xFE
LED0_ON_L  = 0x06

def write8(bus, reg, val):
    bus.write_byte_data(ADDR, reg, val & 0xFF)

def read8(bus, reg):
    return bus.read_byte_data(ADDR, reg)

def set_pwm(bus, ch, on, off):
    base = LED0_ON_L + 4 * ch
    write8(bus, base + 0, on & 0xFF)
    write8(bus, base + 1, (on >> 8) & 0xFF)
    write8(bus, base + 2, off & 0xFF)
    write8(bus, base + 3, (off >> 8) & 0xFF)

def duty(bus, ch, x):  # x: 0.0~1.0
    x = max(0.0, min(1.0, x))
    if x <= 0.0:
        set_pwm(bus, ch, 0, 0)
    elif x >= 1.0:
        # Full on: use off=4096 convention
        set_pwm(bus, ch, 4096, 0)
    else:
        off = int(x * 4095)
        set_pwm(bus, ch, 0, off)

def dig(bus, ch, high: bool):
    duty(bus, ch, 1.0 if high else 0.0)

def set_wheel(bus, u, en, a, b):
    if u > 0:
        dig(bus, a, True);  dig(bus, b, False)
        duty(bus, en, abs(u))
    elif u < 0:
        dig(bus, a, False); dig(bus, b, True)
        duty(bus, en, abs(u))
    else:
        dig(bus, a, False); dig(bus, b, False)
        duty(bus, en, 0.0)

def set_motor(bus, left, right):
    set_wheel(bus, left,  ENA, IN1, IN2)
    set_wheel(bus, right, ENB, IN3, IN4)

def stop_all(bus):
    for ch in range(16):
        duty(bus, ch, 0.0)

def set_frequency(bus, freq_hz):
    # PCA9685 prescale = round(25MHz/(4096*freq)) - 1
    prescale = int(round(25_000_000 / (4096 * freq_hz) - 1))
    old = read8(bus, MODE1)
    sleep = (old & 0x7F) | 0x10  # sleep bit
    write8(bus, MODE1, sleep)
    write8(bus, PRESCALE, prescale)
    write8(bus, MODE1, old)
    time.sleep(0.005)
    write8(bus, MODE1, old | 0x80)  # restart

def main():
    with SMBus(BUS) as bus:
        # 基本初始化
        write8(bus, MODE1, 0x00)
        time.sleep(0.01)
        set_frequency(bus, 200)  # ENA/ENB PWM 建議 100~1000Hz，先 200

        print("Stop all")
        stop_all(bus)
        time.sleep(1)

        s = 0.8
        print("Forward")
        set_motor(bus, s, s)
        time.sleep(2)

        print("Stop")
        set_motor(bus, 0.0, 0.0)
        time.sleep(1)

        print("Backward")
        set_motor(bus, -s, -s)
        time.sleep(2)

        print("Stop")
        set_motor(bus, 0.0, 0.0)
        time.sleep(1)

        print("Spin left")
        set_motor(bus, -s, s)
        time.sleep(2)

        print("Stop")
        set_motor(bus, 0.0, 0.0)
        time.sleep(1)

        print("Spin right")
        set_motor(bus, s, -s)
        time.sleep(2)

        print("Done, stop")
        set_motor(bus, 0.0, 0.0)

if __name__ == "__main__":
    main()
