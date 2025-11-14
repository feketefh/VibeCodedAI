# jarvis_vision.py
import cv2
import threading

# ------------------ YOLO import ------------------
YOLO_AVAILABLE = False
try:
    from ultralytics import YOLO
    from ultralytics.utils import LOGGER
    LOGGER.setLevel("ERROR")
    YOLO_AVAILABLE = True
except Exception:
    print("YOLO import hiba! Objektumfelismerés offline nem működik.")

# ------------------ Egyszeri objektumfelismerés ------------------
def getRecData():
    if not YOLO_AVAILABLE:
        print("YOLO nem elérhető, a kamera modul nem indul.")
        return

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Kamera nem elérhető!")
        return

    try:
        detector = YOLO("models/yolo11s.pt")  # YOLO modell betöltése
    except Exception as e:
        print("YOLO modell betöltési hiba:", e)
        return

    ret, frame = cap.read()
    if not ret:
        print("Kamera olvasási hiba!")
        return
    items = []
    # YOLO feldolgozás
    try:
        results = detector(frame)
        for result in results:
            names = result.names  # class id -> class name mapping

            for cls_id, conf in zip(result.boxes.cls, result.boxes.conf):
                class_name = names[int(cls_id)] if int(cls_id) in names else "Ismeretlen"
                confidence = float(conf)

                # Draw label above rectangle
                label = f"{class_name} ({confidence:.2f})"
                items.append(label)
            return items
    except Exception as e:
        print("YOLO feldolgozási hiba:", e)

# ------------------ Objektumfelismerés elindítása ------------------
def start_vision():
    if not YOLO_AVAILABLE:
        print("YOLO nem elérhető, a kamera modul nem indul.")
        return

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Kamera nem elérhető!")
        return

    try:
        detector = YOLO("models/yolo11s.pt")  # YOLO modell betöltése
    except Exception as e:
        print("YOLO modell betöltési hiba:", e)
        return

    print("Kamera modul elindult. Objektumfelismerés folyamatban...")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Kamera olvasási hiba!")
            break

        # YOLO feldolgozás
        try:
            results = detector(frame)
            for result in results:
                boxes = result.boxes.xyxy
                names = result.names  # class id -> class name mapping

                for box, cls_id, conf in zip(result.boxes.xyxy, result.boxes.cls, result.boxes.conf):
                    x1, y1, x2, y2 = [int(v) for v in box]
                    class_name = names[int(cls_id)] if int(cls_id) in names else "Ismeretlen"
                    confidence = float(conf)

                    # Draw rectangle
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)

                    # Draw label above rectangle
                    label = f"{class_name} ({confidence:.2f})"
                    (label_width, label_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
                    label_y = max(y1 - 10, label_height + 10)

                    cv2.rectangle(frame, (x1, label_y - label_height - 5), (x1 + label_width, label_y + 5), (0,255,0), -1)
                    cv2.putText(frame, label, (x1, label_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 2)
        except Exception as e:
            print("YOLO feldolgozási hiba:", e)

        # Kép megjelenítése
        cv2.imshow("Jarvis Kamera", frame)

        # Kilépés ESC gombbal
        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Kamera modul leállt.")
