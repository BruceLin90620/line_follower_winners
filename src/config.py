# src/config.py

# --- Camera Settings ---
CAM_INDEX = 0
CAM_WIDTH = 640
CAM_HEIGHT = 480
CAM_FPS = 30

# --- Vision Settings ---
# ROI (Region of Interest) - Only process the bottom part of the image
# 0.0 is top, 1.0 is bottom
ROI_Y_START_RATIO = 0.0  
ROI_Y_END_RATIO = 1.0    

# Thresholding
THRESH_VAL = 80          # 0-255, adjust based on lighting
INVERT_THRESH = True     # True for black line on white background (THRESH_BINARY_INV)

# Safety
MIN_CONFIDENCE = 0.00     # Minimum ratio of white pixels to be considered a line

# --- Control Settings ---
CONTROL_HZ = 30          # Frequency of the control loop
BASE_SPEED = 0.2         # 0.0 to 1.0 (Safety base speed)
KP = 0.23                 # Proportional gain
KD = 1.5                # Derivative gain
STEER_LIMIT = 0.5        # Limit steering influence (prevent wheel spin)
SLEW_RATE = 0.3         # Max change in motor output per update (for smooth accel)

# --- PCA9685 Settings ---
PCA_ADDR = 0x40
PCA_FREQ = 200           # Hz, suitable for L298N

I2C_BUS = 7

# --- L298N Hardware Mapping (PCA Channel IDs) ---
# Left Motor
PIN_L_ENA = 0  # PWM
PIN_L_IN1 = 1  # Direction 1
PIN_L_IN2 = 2  # Direction 2

# Right Motor
PIN_R_ENB = 3  # PWM
PIN_R_IN3 = 4  # Direction 1
PIN_R_IN4 = 5  # Direction 2