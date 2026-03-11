import cv2
import numpy as np

# Byt ut siffran mot det index som funkade i förra steget (t.ex. 1)
CAMERA_INDEX = 0 

cap = cv2.VideoCapture(CAMERA_INDEX)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # 1. Konvertera bilden till HSV-färgrymd (lättare för datorn att se färger)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # 2. Definiera färgen du vill spåra (här är ett exempel för en GRÖN boll)
    # Du kommer behöva justera dessa siffror beroende på bollens färg!
    lower_color = np.array([35, 100, 100]) 
    upper_color = np.array([85, 255, 255])

    # 3. Skapa en "mask" (allt som inte är bollens färg blir svart)
    mask = cv2.inRange(hsv, lower_color, upper_color)
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)

    # 4. Hitta konturerna av bollen
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if len(contours) > 0:
        # Hitta den största konturen (förhoppningsvis bollen)
        c = max(contours, key=cv2.contourArea)
        ((x, y), radius) = cv2.minEnclosingCircle(c)
        M = cv2.moments(c)
        
        if M["m00"] > 0:
            center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
            
            # Rita ut en cirkel och koordinaterna på skärmen
            if radius > 10:
                cv2.circle(frame, (int(x), int(y)), int(radius), (0, 255, 255), 2)
                cv2.putText(frame, f"X: {int(x)} Y: {int(y)}", (int(x), int(y)-20), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                
                # Här kommer vi senare lägga till koden för att skicka till Arduino!
                # print(f"Skickar till Arduino: {int(x)}, {int(y)}")

    # Visa resultatet
    cv2.imshow("Bollsparning", frame)
    cv2.imshow("Mask (Datorns syn)", mask)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
