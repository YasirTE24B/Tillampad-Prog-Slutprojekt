import cv2
import numpy as np
import serial
import time
import threading
from flask import Flask, jsonify, request
from flask_cors import CORS

# --- GLOBALA VARIABLER ---
shared_data = {"ball_x": 320} 
is_dead_status = 0 

# --- FLASK SETUP ---
app = Flask(__name__)
CORS(app) 

# --- VISION SETUP ---
# Försök med index 0, 1 eller 2 beroende på din kamera
cap = cv2.VideoCapture(2, cv2.CAP_DSHOW) 
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
# cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25) # Aktivera om FPS svajar

try:
    arduino = serial.Serial(port='COM3', baudrate=115200, timeout=0)
    print("Arduino Connected!")
    time.sleep(2)
except Exception as e:
    print(f"Arduino NOT found: {e}")
    arduino = None

# Färgmask för orange pingisboll
lower_ball = np.array([0, 79, 175]) 
upper_ball = np.array([30, 255, 255])

def vision_worker():
    global shared_data, is_dead_status
    last_time = time.time() 

    while True:
        ret, frame = cap.read()
        if not ret: break

        # Räkna FPS
        now = time.time()
        dt = now - last_time
        last_time = now
        if dt > 0 and np.random.random() > 0.95:
            print(f"Kameran kör i: {1/dt:.1f} FPS")

        # Bildanalys
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, lower_ball, upper_ball)
        mask = cv2.erode(mask, None, iterations=1)
        mask = cv2.dilate(mask, None, iterations=1)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            c = max(contours, key=cv2.contourArea)
            if cv2.contourArea(c) > 300:
                M = cv2.moments(c)
                if M['m00'] > 0:
                    ball_x = int(M['m10'] / M['m00'])
                    ball_y = int(M['m01'] / M['m00'])
                    shared_data["ball_x"] = ball_x
                    
                    # Rita spårning
                    cv2.circle(frame, (ball_x, ball_y), 20, (0, 255, 0), 2)
                    cv2.putText(frame, f"X: {ball_x}", (ball_x, ball_y-25), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    
                    if arduino:
                        # Skicka X och status till Arduino
                        arduino.write(f"{ball_x},{is_dead_status}\n".encode())

        # Läs från Arduino
        if arduino and arduino.in_waiting > 0:
            try:
                line = arduino.readline().decode('utf-8').strip()
                if line: print(f"Arduino: {line}")
            except: pass

        cv2.line(frame, (320, 0), (320, 480), (0, 0, 255), 1)
        cv2.imshow("OpenCV Stream", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

    cap.release()
    cv2.destroyAllWindows()

# --- ROUTES ---
@app.route('/get_ball')
def get_ball():
    return jsonify(shared_data)

@app.route('/set_status')
def set_status():
    global is_dead_status
    try:
        is_dead_status = int(request.args.get('dead', 0))
    except: pass
    return "OK"

if __name__ == '__main__':
    threading.Thread(target=vision_worker, daemon=True).start()
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    print("Server startad på http://localhost:5000")
    app.run(port=5000, debug=False, threaded=True)