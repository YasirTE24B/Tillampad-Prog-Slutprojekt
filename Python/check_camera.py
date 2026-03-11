import cv2

def scan_for_camo():
    # We check both MSMF and DSHOW backends for the first 10 indexes
    backends = [cv2.CAP_MSMF, cv2.CAP_DSHOW]
    
    for backend in backends:
        backend_name = "MSMF" if backend == cv2.CAP_MSMF else "DSHOW"
        print(f"--- Checking {backend_name} Backend ---")
        
        for i in range(5):
            cap = cv2.VideoCapture(i + backend)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    window_name = f"Index {i} on {backend_name}"
                    cv2.imshow(window_name, frame)
                    print(f"Found camera at index {i} using {backend_name}")
                    cv2.waitKey(2000) # Shows each camera for 2 seconds
                    cv2.destroyWindow(window_name)
                cap.release()

scan_for_camo()
cv2.destroyAllWindows()