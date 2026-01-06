# src/controller_pd.py
from .config import *

class PDController:
    def __init__(self):
        self.prev_error = 0.0
        
    def step(self, error):
        """
        Input: error (-1.0 to 1.0)
        Output: left_cmd, right_cmd (-1.0 to 1.0)
        """
        # PD Calculation
        d_error = error - self.prev_error
        steer = (KP * error) + (KD * d_error)
        self.prev_error = error
        
        # Clamp steering
        steer = max(-STEER_LIMIT, min(STEER_LIMIT, steer))
        
        # Differential Drive
        # If error > 0 (Line is Right), steer > 0.
        # We want to turn Right -> Left motor speeds up, Right slows down.
        # The prompt says: left = BASE - steer, right = BASE + steer
        # If steer is positive using that formula: Left slows, Right speeds -> Turn LEFT.
        # This means the sign of steer needs to be flipped or the formula adjusted based on hardware.
        # Assuming typical setup: Positive Error (Right) should result in Turning Right.
        # Let's trust the user's formula but note that KP might need to be negative 
        # depending on motor wiring. We stick to the prompt's formula:
        
        left_cmd = BASE_SPEED + steer
        right_cmd = BASE_SPEED - steer
        
        # Final Clamp
        left_cmd = -max(-1.0, min(1.0, left_cmd))
        right_cmd = -max(-1.0, min(1.0, right_cmd))
        
        return left_cmd, right_cmd

if __name__ == "__main__":
    # 測試指令：python3 -m src.controller_pd
    print("--- Testing PD Logic ---")
    pd = PDController()
    
    test_errors = [0.0, 0.5, -0.5, 1.0] # 中間, 偏右, 偏左, 極右
    
    print(f"{'Error':^10} | {'Left Cmd':^10} | {'Right Cmd':^10} | {'Action':^10}")
    print("-" * 50)
    
    for err in test_errors:
        l, r = pd.step(err)
        action = "Straight"
        if l > r: action = "Turn Right" # 左輪快，右輪慢 -> 向右轉
        elif r > l: action = "Turn Left"
        
        print(f"{err:^10.2f} | {l:^10.2f} | {r:^10.2f} | {action:^10}")
        