import os
import cv2
import time

# ===========================
# Capture Face Images
# ===========================

class FaceCapture:

    def __init__(self,
                 save_folder,
                 total_images=100):

        self.save_folder = save_folder
        self.total_images = total_images

        os.makedirs(save_folder, exist_ok=True)

        self.camera = cv2.VideoCapture(0)

        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        self.face_detector = cv2.CascadeClassifier(
            cv2.data.haarcascades +
            "haarcascade_frontalface_default.xml"
        )

    # ===========================

    def capture(self):

        count = 0

        print("\nStarting Face Capture...\n")

        time.sleep(2)

        while True:

            ret, frame = self.camera.read()

            if not ret:
                break

            gray = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2GRAY
            )

            faces = self.face_detector.detectMultiScale(
                gray,
                1.3,
                5
            )

            for (x, y, w, h) in faces:

                face = frame[y:y+h, x:x+w]

                face = cv2.resize(
                    face,
                    (200, 200)
                )

                filename = os.path.join(
                    self.save_folder,
                    f"{count}.jpg"
                )

                cv2.imwrite(filename, face)

                count += 1

                cv2.rectangle(
                    frame,
                    (x, y),
                    (x+w, y+h),
                    (0,255,0),
                    2
                )

                cv2.putText(
                    frame,
                    f"Captured : {count}/{self.total_images}",
                    (20,40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0,255,255),
                    2
                )

                time.sleep(0.05)

            cv2.imshow(
                "Face Registration",
                frame
            )

            key = cv2.waitKey(1)

            if key == ord("q"):
                break

            if count >= self.total_images:
                break

        self.camera.release()

        cv2.destroyAllWindows()

        print("\nFace Capture Completed.")