import os
import pickle
import tempfile
import face_recognition

# ==========================
# Folder Paths
# ==========================

DATASET_PATH = "dataset/faces"
OUTPUT_FILE = "models/face_encodings.pkl"

known_face_encodings = []
known_face_names = []


# ==========================
# Train Faces
# ==========================

def train_faces():

    print("=" * 50)
    print("      AI FACE TRAINING STARTED")
    print("=" * 50)

    global known_face_encodings, known_face_names
    known_face_encodings = []
    known_face_names = []

    total_students = 0
    total_images = 0

    if not os.path.exists(DATASET_PATH):
        print("Dataset folder not found.")
        return

    for student_name in sorted(os.listdir(DATASET_PATH)):

        student_folder = os.path.join(DATASET_PATH, student_name)

        if not os.path.isdir(student_folder):
            continue

        print(f"\nTraining: {student_name}")

        total_students += 1

        for image_name in sorted(os.listdir(student_folder)):

            image_path = os.path.join(student_folder, image_name)
            if not image_name.lower().endswith((".jpg", ".jpeg", ".png")):
                continue

            try:

                image = face_recognition.load_image_file(image_path)

                face_locations = face_recognition.face_locations(image)
                if len(face_locations) != 1:
                    print(f"   ✗ Expected one face -> {image_name}")
                    continue

                encodings = face_recognition.face_encodings(image, face_locations)

                if len(encodings) > 0:

                    known_face_encodings.append(encodings[0])

                    known_face_names.append(student_name)

                    total_images += 1

                    print(f"   ✓ {image_name}")

                else:

                    print(f"   ✗ No face found -> {image_name}")

            except Exception as error:

                print(f"Error processing {image_name}: {error}")

    # Save encodings

    data = {

        "encodings": known_face_encodings,

        "names": known_face_names

    }

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    temporary_file = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=os.path.dirname(OUTPUT_FILE),
            delete=False
        ) as file:
            temporary_file = file.name
            pickle.dump(data, file)
        os.replace(temporary_file, OUTPUT_FILE)
    finally:
        if temporary_file and os.path.exists(temporary_file):
            os.remove(temporary_file)

    print("\n")
    print("=" * 50)
    print("Training Completed")
    print("=" * 50)

    print(f"Students : {total_students}")
    print(f"Images   : {total_images}")

    print(f"\nSaved Model -> {OUTPUT_FILE}")


# ==========================

if __name__ == "__main__":

    train_faces()