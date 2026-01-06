# src/motors_l298n.py
from .config import *

class L298NMotor:
    def __init__(self, pca, pwm_pin, in1_pin, in2_pin):
        self.pca = pca
        self.pwm_pin = pwm_pin
        self.in1_pin = in1_pin
        self.in2_pin = in2_pin
        self.current_speed = 0.0

    def set_target(self, target_speed):
        """
        設定目標速度 (-1.0 ~ 1.0)
        結合 Slew Rate (平滑) 與 Deadzone Compensation (起步補償)
        """
        target_speed = max(-0.8, min(0.8, target_speed))

        # --- 1. Slew Rate 平滑運算 ---
        # 如果 SLEW_RATE > 0，就慢慢靠近目標
        if SLEW_RATE > 0.0:
            delta = target_speed - self.current_speed
            if abs(delta) > SLEW_RATE:
                if delta > 0:
                    self.current_speed += SLEW_RATE
                else:
                    self.current_speed -= SLEW_RATE
            else:
                self.current_speed = target_speed
        else:
            self.current_speed = target_speed

        # --- 2. 寫入硬體 ---
        self._write_hardware(self.current_speed)

    def _write_hardware(self, speed):
        """
        底層硬體控制 (含起步補償)
        """
        # --- 【關鍵修改】起步補償 ---
        # 馬達通常在 PWM 0.3 以下推不動。
        # 所以只要速度不是 0，我們就強制把它拉高到至少 0.3 (30%)
        MIN_POWER = 0.21  # 你可以根據車子重量調整 (0.3 ~ 0.4)
        
        abs_speed = abs(speed)
        
        # 如果速度很小 (代表要停)，就直接給 0
        if abs_speed < 0.05:
            final_pwm = 0.0
        else:
            # 如果要動，取 (目前速度) 和 (最小推力) 的最大值
            # 這樣起步會直接跳到 0.35，避開推不動的區域
            final_pwm = max(abs_speed, MIN_POWER)

        # 寫入 PCA9685
        if speed > 0.05: # 正轉
            self.pca.dig(self.in1_pin, True)
            self.pca.dig(self.in2_pin, False)
            self.pca.duty(self.pwm_pin, final_pwm)
            
        elif speed < -0.05: # 反轉
            self.pca.dig(self.in1_pin, False)
            self.pca.dig(self.in2_pin, True)
            self.pca.duty(self.pwm_pin, final_pwm)
            
        else: # 停止
            self.pca.dig(self.in1_pin, False)
            self.pca.dig(self.in2_pin, False)
            self.pca.duty(self.pwm_pin, 0.0)

class MotorDriver:
    def __init__(self, pca):
        self.pca = pca
        self.left = L298NMotor(pca, PIN_L_ENA, PIN_L_IN1, PIN_L_IN2)
        self.right = L298NMotor(pca, PIN_R_ENB, PIN_R_IN3, PIN_R_IN4)

    def set(self, left_speed, right_speed):
        self.left.set_target(left_speed)
        self.right.set_target(right_speed)

    def stop(self):
        self.left.set_target(0)
        self.right.set_target(0)