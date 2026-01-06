# src/controller_pd.py
from .config import *


class PDController:
    """
    PD 控制器（用於循跡/偏差修正）
    - 輸入：error（-1.0 ~ 1.0），代表偏離中心的誤差
    - 輸出：left_cmd, right_cmd（理想上 -1.0 ~ 1.0），給左右輪的速度指令
    """

    def __init__(self):
        # 上一次的誤差，用於計算微分項 D
        self.prev_error = 0.0

    def step(self, error: float):
        """
        計算一次控制輸出
        :param error: 當前誤差（-1.0 ~ 1.0）
        :return: (left_cmd, right_cmd)
        """

        # ===== 1) PD 計算 =====
        # P 項：KP * error
        # D 項：KD * (error - prev_error)
        d_error = error - self.prev_error
        steer = (KP * error) + (KD * d_error)

        # 更新 prev_error，供下次 step 使用
        self.prev_error = error

        # ===== 2) 轉向量限制（避免轉太大）=====
        steer = max(-STEER_LIMIT, min(STEER_LIMIT, steer))

        # ===== 3) 差速控制（Differential Drive）=====
        left_cmd = BASE_SPEED + steer
        right_cmd = BASE_SPEED - steer

        # ===== 4) 最終輸出限制到 [-1.0, 1.0] =====
        left_cmd = max(-1.0, min(1.0, left_cmd))
        right_cmd = max(-1.0, min(1.0, right_cmd))

        left_cmd = -left_cmd
        right_cmd = -right_cmd

        return left_cmd, right_cmd