# SmartAICamera
This project is an AI-powered Face Recognition and Emotion Detection System built with Flask. It uses OpenCV and the face_recognition library for face detection and recognition, and a pre-trained TensorFlow model for emotion analysis.
---------------------
# AI Camera - Face Recognition & Emotion Detection

## 📌 Overview

AI Camera is a web-based system for **face recognition and emotion detection**.
It combines **OpenCV**, **face\_recognition**, and a **TensorFlow deep learning model** to provide real-time analysis of human faces and their emotions.

This project can be used for:

* Security systems
* User interaction analysis
* Intelligent assistants
* Research and educational purposes

---

## 🚀 Features

* Real-time **face detection** and recognition
* **Emotion detection** using a pre-trained deep learning model (`emotion_model.h5`)
* Web-based interface built with **Flask**
* Simple and responsive **frontend (HTML, CSS, JS)**
* REST API for integration with other applications
* Works both with **TensorFlow** (for real predictions) and without (simulation mode)

---

## 🛠️ Technologies Used

* **Python 3**
* **Flask** + **Flask-CORS**
* **OpenCV** (cv2)
* **face\_recognition** library
* **TensorFlow / Keras**
* **NumPy**, **Pillow**
* **HTML**, **CSS**, **JavaScript**

---

## 📂 Project Structure

```
aicamera/
│── backend.py          # Flask backend for face & emotion detection
│── run.py              # Application launcher
│── emotion_model.h5    # Pre-trained deep learning model for emotion detection
│── requirements.txt    # Dependencies
│── templates/          # HTML templates (index.html)
│── styles.css          # Frontend styles
│── script.js           # Frontend logic
│── start.bat           # Windows quick launcher
│── j3(image-processing).ipynb  # Jupyter notebook for experiments
```

---

## ⚡ Installation

1. Clone the repository or extract the project files:

   ```bash
   git clone <repository-url>
   cd aicamera
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. (Optional) If you don’t have GPU support, install CPU-only TensorFlow:

   ```bash
   pip install tensorflow-cpu==2.13.0
   ```

---

## ▶️ Usage

Run the application:

```bash
python run.py
```

Then open your browser at:

```
http://127.0.0.1:5000/
```

The system will automatically access your **webcam** for real-time face recognition and emotion detection.

---

## 📌 Notes

* Requires a **webcam** for real-time detection.
* If TensorFlow is not installed, the system will still run but with **simulated emotions**.
* You can replace the provided `emotion_model.h5` with your own trained model for better accuracy.
* For Windows, you can use `start.bat` to quickly launch the system.

---

## 🧩 Future Improvements

* Add a **database** to store recognized faces and detected emotions.
* Implement **user management** and login system.
* Improve frontend with a more advanced UI.
* Support for multiple cameras.
* Add logging and analytics dashboard.

---

## 📜 License

This project is for **educational and research purposes only**. Feel free to modify and improve it for your own use.
