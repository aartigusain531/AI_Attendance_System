import cv2
import face_recognition
import pickle
import os

# ==============================
# Load Trained Face Encodings
# ==============================

MODEL_FILE = "models/face_encodings.pkl"
known_face_encodings = []
known_face_names = []


def load_face_encodings():
    if not os.path.exists(MODEL_FILE):
        return [], []

    with open(MODEL_FILE, "rb") as f:
        data = pickle.load(f)
        return data.get("encodings", []), data.get("names", [])


known_face_encodings, known_face_names = load_face_encodings()

if not known_face_encodings:
    print("Face model not found or empty. Starting with no known faces.")


# ==============================
# Face Recognition Class
# ==============================

class FaceRecognizer:

    def __init__(self):

        self.camera = cv2.VideoCapture(0)

        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    def recognize(self):

        recognized_name = None

        while True:

            ret, frame = self.camera.read()

            if not ret:
                break

            # Resize frame for faster processing
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

            rgb_small = cv2.cvtColor(
                small_frame,
                cv2.COLOR_BGR2RGB
            )

            face_locations = face_recognition.face_locations(rgb_small)

            face_encodings = face_recognition.face_encodings(
                rgb_small,
                face_locations
            )

            for (top, right, bottom, left), face_encoding in zip(
                face_locations,
                face_encodings
            ):

                matches = face_recognition.compare_faces(
                    known_face_encodings,
                    face_encoding,
                    tolerance=0.45
                )

                name = "Unknown"

                face_distances = face_recognition.face_distance(
                    known_face_encodings,
                    face_encoding
                )

                if len(face_distances) > 0:

                    best_match = face_distances.argmin()

                    if matches[best_match]:

                        name = known_face_names[best_match]
                        recognized_name = name

                # Scale coordinates back
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4

                color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)

                cv2.rectangle(
                    frame,
                    (left, top),
                    (right, bottom),
                    color,
                    2
                )

                cv2.rectangle(
                    frame,
                    (left, bottom - 35),
                    (right, bottom),
                    color,
                    cv2.FILLED
                )

                cv2.putText(
                    frame,
                    name,
                    (left + 6, bottom - 8),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (255, 255, 255),
                    2
                )

            cv2.imshow(
                "AI Face Recognition",
                frame
            )

            key = cv2.waitKey(1)

            # Press Q to quit
            if key == ord("q"):
                break

            # Press Enter when a known face is detected
            if recognized_name and key == 13:
                break

        self.camera.release()
        cv2.destroyAllWindows()

        return recognized_name


# ==============================

if __name__ == "__main__":

    recognizer = FaceRecognizer()

    person = recognizer.recognize()

    if person:
        print(f"\nRecognized : {person}")
    else:
        print("\nNo recognized face.")