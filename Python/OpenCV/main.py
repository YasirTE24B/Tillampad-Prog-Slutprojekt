import cv2
import numpy as np
import serial
import time
import threading
from flask import Flask, jsonify, request
from flask_cors import CORS

shared_data = {"ball_x": 320} 
is_dead_status = 0 

# Flask
app = Flask(__name__)
CORS(app) 

cap = cv2.VideoCapture(2, cv2.CAP_DSHOW) 
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
# cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25) # Aktivera om 15fps

try:
    arduino = serial.Serial(port='COM3', baudrate=115200, timeout=0)
    print("Arduino Connected!")
    time.sleep(2)
except Exception as e:
    print(f"Arduino NOT found: {e}")
    arduino = None

lower_ball = np.array([0, 79, 175]) 
upper_ball = np.array([30, 255, 255])

def vision_worker():
    global shared_data, is_dead_status
    last_time = time.time() 

    while True:
        ret, frame = cap.read()
        if not ret: break

        # räkna FPS (kan kommentera ut)
        now = time.time()
        dt = now - last_time
        last_time = now
        if dt > 0 and np.random.random() > 0.95:
            print(f"Kameran kör i: {1/dt:.1f} FPS")

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
                    
                    # måla ut bollen
                    cv2.circle(frame, (ball_x, ball_y), 20, (0, 255, 0), 2)
                    cv2.putText(frame, f"X: {ball_x}", (ball_x, ball_y-25), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    
                    if arduino:
                        # Skicka X och status till Arduino
                        arduino.write(f"{ball_x},{is_dead_status}\n".encode())

        # Läs från Arduino
        if arduino and arduino.in_waiting > 0:
            try:
                # läs ALLA rader som ligger och väntar för att tömma kön
                while arduino.in_waiting > 0:
                    line = arduino.readline().decode('utf-8').strip()

                if line: 
                    if line.isdigit(): #viktigt för debug mode men måste se till att jag endast serial println pot värden annars kommer det inte bli bra
                        shared_data["ball_x"] = int(line)
                        print(f"Arduino NUMMER: {line}")
                    else:
                        print(f"Arduino: {line}") #arduino serial monitor saker noteras såhär
            except Exception as e:
                print(f"Serial error: {e}")
                pass

        cv2.line(frame, (320, 0), (320, 480), (0, 0, 255), 1)
        cv2.imshow("OpenCV Stream", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

    cap.release()
    cv2.destroyAllWindows()




# routes och sånt
@app.route('/get_ball')
def get_ball():
    return jsonify(shared_data)

@app.route('/set_status')
def set_status():
    global is_dead_status
    is_dead_status = int(request.args.get('dead', 0))
    if arduino:
        if is_dead_status == 1:
            arduino.write(b"D\n") # skicka D för död till arduino
        else:
            arduino.write(b"L\n") # skicka L för lever till arduino
    return "OK"

@app.route('/trigger_point')
def trigger_point():
    if arduino:
        arduino.write(b"P\n") # skicka till arduino
    return "OK"

if __name__ == '__main__':
    threading.Thread(target=vision_worker, daemon=True).start()
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    print("Server startad på http://localhost:5000")
    app.run(port=5000, debug=False, threaded=True)