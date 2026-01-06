# src/main.py
import cv2
import time
import sys
import traceback

# Relative imports for module execution
from .config import *
from .pca9685_smbus import PCA9685, find_pca_bus
from .motors_l298n import MotorDriver
from .camera_usb import Camera
from .vision_line import Vision
from .controller_pd import PDController

def main():
    print("Initializing Line Follower...")
    
    # 1. Hardware Init
    bus_num = find_pca_bus(PCA_ADDR)
    if bus_num is None:
        print("Error: PCA9685 not found.")
        return

    pca = PCA9685(bus_num, PCA_ADDR)
    pca.set_frequency(PCA_FREQ)
    motors = MotorDriver(pca)
    
    try:
        cam = Camera()
    except RuntimeError as e:
        print(e)
        return

    vision = Vision()
    controller = PDController()

    print("System Ready. Press 'q' in window or Ctrl+C to stop.")
    
    # Timing variables
    dt = 1.0 / CONTROL_HZ
    last_time = time.time()
    
    try:
        while True:
            # Loop Timing
            now = time.time()
            if now - last_time < dt:
                time.sleep(0.001) # Yield slightly
                continue
            last_time = now

            # 1. Perception
            ret, frame = cam.read()
            if not ret:
                print("Failed to capture image")
                break
                
            error, conf, mask, debug = vision.process(frame)
            
            # 2. Safety & Control
            if conf < MIN_CONFIDENCE:
                print(f"Lost Line! (Conf: {conf:.2f}) - STOP")
                motors.stop()
            else:
                left, right = controller.step(error)
                motors.set(left, right)
                print(f"Err: {error:.2f} | L: {left:.2f} | R: {right:.2f}")

            # 3. Visualization
            # cv2.imshow("Debug", debug)
            # cv2.imshow("Mask", mask)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        print("\nCtrl+C detected.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        traceback.print_exc()
    finally:
        print("Cleaning up...")
        motors.stop()
        pca.stop_all()
        cam.close()
        cv2.destroyAllWindows()
        print("Stopped safely.")

if __name__ == "__main__":
    main()