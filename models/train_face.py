import os
import pickle
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

    total_students = 0
    total_images = 0

    if not os.path.exists(DATASET_PATH):
        print("Dataset folder not found.")
        return

    for student_name in os.listdir(DATASET_PATH):

        student_folder = os.path.join(DATASET_PATH, student_name)

        if not os.path.isdir(student_folder):
            continue

        print(f"\nTraining: {student_name}")

        total_students += 1

        for image_name in os.listdir(student_folder):

            image_path = os.path.join(student_folder, image_name)

            try:

                image = face_recognition.load_image_file(image_path)

                encodings = face_recognition.face_encodings(image)

                if len(encodings) > 0:

                    known_face_encodings.append(encodings[0])

                    known_face_names.append(student_name)

                    total_images += 1

                    print(f"   ✓ {image_name}")

                else:

                    print(f"   ✗ No face found -> {image_name}")

            except Exception as e:

                print(f"Error : {image_name}")

    # Save encodings

    data = {

        "encodings": known_face_encodings,

        "names": known_face_names

    }

    with open(OUTPUT_FILE, "wb") as file:

        pickle.dump(data, file)

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