# src/motors_l298n.py
from .config import *


class L298NMotor:
    """
    單顆 L298N 馬達控制（使用 PCA9685 產生 PWM 與方向腳位）
    - pwm_pin: 連到 L298N 的 ENA/ENB（PWM）
    - in1_pin, in2_pin: 連到 L298N 的 IN1/IN2（方向）
    """

    # ===== 行為門檻（保留原本數值，集中管理）=====
    SPEED_LIMIT = 0.8        # set_target 會把輸入速度限制在 [-0.8, 0.8]
    STOP_EPS = 0.05          # 小於此速度視為停止（方向判斷與起步補償都用到）
    MIN_POWER = 0.21         # 起步補償最小推力（只要不是停，就至少給這個 PWM）

    def __init__(self, pca, pwm_pin: int, in1_pin: int, in2_pin: int):
        self.pca = pca
        self.pwm_pin = pwm_pin
        self.in1_pin = in1_pin
        self.in2_pin = in2_pin

        # 目前速度（會被 slew rate 逐步逼近目標）
        self.current_speed = 0.0

    def set_target(self, target_speed: float) -> None:
        """
        設定目標速度（-1.0 ~ 1.0，實際會限制到 [-0.8, 0.8]）
        功能包含：
        1) Slew Rate（平滑加減速，避免瞬間跳變）
        2) Deadzone / 起步補償（避免 PWM 太小推不動）
        """
        # --- 0) 限幅：避免速度過大（保留你原本 -0.8~0.8 的限制）---
        target_speed = max(-self.SPEED_LIMIT, min(self.SPEED_LIMIT, target_speed))

        # --- 1) Slew Rate 平滑運算 ---
        # 若 SLEW_RATE > 0：每次呼叫最多只改變 SLEW_RATE，讓速度逐步靠近 target
        if SLEW_RATE > 0.0:
            delta = target_speed - self.current_speed

            if abs(delta) > SLEW_RATE:
                self.current_speed += SLEW_RATE if delta > 0 else -SLEW_RATE
            else:
                self.current_speed = target_speed
        else:
            # 若 SLEW_RATE <= 0：直接等於目標速度（不平滑）
            self.current_speed = target_speed

        # --- 2) 寫入硬體 ---
        self._write_hardware(self.current_speed)

    def _write_hardware(self, speed: float) -> None:
        """
        寫入 PCA9685（方向腳位 + PWM）
        同時包含「起步補償」：
        - 馬達在很低 PWM 時可能推不動
        - 只要不是停止，就至少給 MIN_POWER
        """
        abs_speed = abs(speed)

        # --- 起步補償（保留你原本的邏輯與數值）---
        # 速度很小 => 當作要停
        if abs_speed < self.STOP_EPS:
            final_pwm = 0.0
        else:
            # 要動 => PWM 至少 MIN_POWER
            final_pwm = max(abs_speed, self.MIN_POWER)

        # --- 方向控制 + PWM 輸出 ---
        if speed > self.STOP_EPS:
            # 正轉：IN1=1, IN2=0
            self.pca.dig(self.in1_pin, True)
            self.pca.dig(self.in2_pin, False)
            self.pca.duty(self.pwm_pin, final_pwm)

        elif speed < -self.STOP_EPS:
            # 反轉：IN1=0, IN2=1
            self.pca.dig(self.in1_pin, False)
            self.pca.dig(self.in2_pin, True)
            self.pca.duty(self.pwm_pin, final_pwm)

        else:
            # 停止：IN1=0, IN2=0，PWM=0
            self.pca.dig(self.in1_pin, False)
            self.pca.dig(self.in2_pin, False)
            self.pca.duty(self.pwm_pin, 0.0)


class MotorDriver:
    """
    雙輪馬達驅動器封裝：
    - left: 左輪（ENA + IN1/IN2）
    - right: 右輪（ENB + IN3/IN4）
    """

    def __init__(self, pca):
        self.pca = pca

        # 左右輪腳位由 config.py 提供（保留你原本的 mapping）
        self.left = L298NMotor(pca, PIN_L_ENA, PIN_L_IN1, PIN_L_IN2)
        self.right = L298NMotor(pca, PIN_R_ENB, PIN_R_IN3, PIN_R_IN4)

    def set(self, left_speed: float, right_speed: float) -> None:
        """
        設定左右輪速度（-1.0 ~ 1.0）
        內部會套用各自的 slew rate 與起步補償
        """
        self.left.set_target(left_speed)
        self.right.set_target(right_speed)

    def stop(self) -> None:
        """停止左右輪（等同 set(0, 0)）"""
        self.left.set_target(0.0)
        self.right.set_target(0.0)
