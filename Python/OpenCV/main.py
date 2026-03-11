import cv2
import serial
import time
import numpy as np

# --- INITIAL SETUP ---
# Adjust COM port for your Arduino
try:
    arduino = serial.Serial(port='COM3', baudrate=9600, timeout=.01)
    time.sleep(2)
except:
    print("Warning: Arduino not connected.")
    arduino = None

cap = cv2.VideoCapture(1 + cv2.CAP_MSMF)

# PID Variables
prev_error = 0
integral = 0

# --- TUNING WINDOW ---
cv2.namedWindow("Tuning", cv2.WINDOW_NORMAL) # WINDOW_NORMAL makes it resizable
cv2.resizeWindow("Tuning", 400, 600)

def nothing(x): pass

# Color Sliders (Blue)
cv2.createTrackbar("Low H", "Tuning", 100, 179, nothing)
cv2.createTrackbar("High H", "Tuning", 140, 179, nothing)
# PID Sliders (Values multiplied by 100 in code for precision)
cv2.createTrackbar("Kp", "Tuning", 20, 200, nothing)  # Start with 0.2
cv2.createTrackbar("Ki", "Tuning", 0, 100, nothing)
cv2.createTrackbar("Kd", "Tuning", 10, 200, nothing) # Start with 0.1
# Boundary Sliders
cv2.createTrackbar("Boundary X", "Tuning", 200, 300, nothing)

# Set main windows to be resizable
cv2.namedWindow("PID Tracking", cv2.WINDOW_NORMAL)
cv2.namedWindow("Mask", cv2.WINDOW_NORMAL)

while True:
    ret, frame = cap.read()
    if not ret: break

    h, w, _ = frame.shape
    center_x = w // 2
    center_y = h // 2

    # 1. Get Values from Sliders
    lh = cv2.getTrackbarPos("Low H", "Tuning")
    hh = cv2.getTrackbarPos("High H", "Tuning")
    kp = cv2.getTrackbarPos("Kp", "Tuning") / 100.0
    ki = cv2.getTrackbarPos("Ki", "Tuning") / 1000.0 # Ki is usually very small
    kd = cv2.getTrackbarPos("Kd", "Tuning") / 100.0
    limit = cv2.getTrackbarPos("Boundary X", "Tuning")

    # 2. Process Image
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array([lh, 100, 100]), np.array([hh, 255, 255]))
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # 3. Draw Static Visuals (Center Dot & Boundaries)
    cv2.circle(frame, (center_x, center_y), 7, (0, 255, 0), -1) # Green Dot
    cv2.line(frame, (center_x - limit, 0), (center_x - limit, h), (0, 0, 255), 2) # Left Limit
    cv2.line(frame, (center_x + limit, 0), (center_x + limit, h), (0, 0, 255), 2) # Right Limit

    if contours:
        largest = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest) > 400:
            M = cv2.moments(largest)
            if M["m00"] != 0:
                ball_x = int(M["m10"] / M["m00"])
                ball_y = int(M["m01"] / M["m00"])

                # Draw Ball Center Dot
                cv2.circle(frame, (ball_x, ball_y), 10, (255, 0, 0), -1)

                # 4. PID Logic
                error = center_x - ball_x
                
                # Only run PID if ball is within red boundaries
                if abs(error) < limit:
                    integral += error
                    derivative = error - prev_error
                    output = (kp * error) + (ki * integral) + (kd * derivative)
                    
                    servo_angle = 90 + output
                    servo_angle = max(40, min(140, int(servo_angle))) # Safe servo range
                    
                    if arduino:
                        arduino.write(f"{servo_angle}\n".encode())
                    
                    prev_error = error
                    cv2.putText(frame, f"Angle: {servo_angle}", (50, 50), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    cv2.imshow('PID Tracking', frame)
    cv2.imshow('Mask', mask)
    
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()
if arduino: arduino.close()