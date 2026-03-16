# FaceRecognitionSystem
# 🛡️ Face Recognition Security System

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green?style=for-the-badge&logo=opencv&logoColor=white)
![Tkinter](https://img.shields.io/badge/GUI-Tkinter-orange?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

An AI-powered real-time face recognition security system with a modern dark-themed GUI. Detect, register, and identify faces through your webcam — with automatic access logging and a full management dashboard.

---

## ✨ Features

- 🎥 **Live Webcam Feed** — Real-time mirrored camera display with face bounding boxes and identity labels
- 👤 **Face Registration** — Auto-captures 50 face samples per person for high-accuracy recognition
- 🔍 **Face Recognition** — LBPH-based recognizer with confidence scoring displayed on screen
- 🔒 **Security Monitoring Mode** — Continuously monitors live feed and logs every access attempt
- 📋 **Access Logs** — Every recognized/unknown face is timestamped and logged to `access_log.txt`
- 👥 **Face Management** — View and delete registered users directly from the GUI
- 💾 **Persistent Storage** — Registered faces and model data are saved to `security_data.pkl`
- 🎨 **Modern Dark UI** — Polished dark-themed interface built with Tkinter and custom styling

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.8+ |
| Face Detection | OpenCV Haar Cascades |
| Face Recognition | OpenCV LBPH (`cv2.face.LBPHFaceRecognizer`) |
| GUI Framework | Tkinter + ttk |
| Image Display | Pillow (PIL) |
| Data Storage | Pickle (`.pkl`) |
| Logging | Plain text (`access_log.txt`) |

---

## 📁 Project Structure

```
FaceRecognitionSystem/
│
├── main.py                  # Main application entry point
├── security_data.pkl        # Saved face encodings (auto-generated)
├── access_log.txt           # Access attempt logs (auto-generated)
└── README.md
```

---

## ⚙️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Kenk26/FaceRecognitionSystem.git
cd FaceRecognitionSystem
```

### 2. Install Dependencies

```bash
pip install opencv-contrib-python numpy pillow
```

> ⚠️ **Important:** You must install `opencv-contrib-python` (not just `opencv-python`) — the LBPH face recognizer is only available in the `contrib` package.

### 3. Run the Application

```bash
python main.py
```

---

## 🚀 How to Use

### Register a New Face
1. Click **➕ Register New Face**
2. Enter the person's name in the dialog
3. Look directly at the camera — the system will **auto-capture 50 samples**
4. Registration completes automatically once all samples are collected

### Start Monitoring
1. Ensure at least one face is registered
2. Click **🔒 Start Monitoring**
3. The system will detect and identify faces in real time
4. Access is logged as **GRANTED** (known face) or **DENIED** (unknown face)

### View Logs
- Click **📋 View Access Logs** to see the last 50 access attempts
- Logs also appear live in the sidebar panel during monitoring

### Manage Registered Faces
- Click **👥 Manage Faces** to view all registered users
- Select a user and click **Delete Selected** to remove them

---

## 📊 How It Works

```
Webcam Frame
     │
     ▼
Haar Cascade Face Detection
     │
     ▼
Extract Face ROI → Resize to 200×200
     │
     ├── Registration Mode → Collect 50 samples → Train LBPH Model
     │
     └── Monitoring Mode  → LBPH Predict → Confidence Score
                                │
                    ┌───────────┴───────────┐
                 < 50 conf              ≥ 50 conf
                (Known Face)          (Unknown Face)
                    │                      │
               Log GRANTED            Log DENIED
```

> The confidence threshold is set to **50** (lower = stricter). A 30-frame cooldown prevents duplicate log entries for the same face.

---

## 📦 Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `opencv-contrib-python` | 4.x | Face detection & LBPH recognition |
| `numpy` | Latest | Array operations for face data |
| `Pillow` | Latest | Converting OpenCV frames for Tkinter display |
| `tkinter` | Built-in | GUI framework |
| `pickle` | Built-in | Saving/loading face data |

---

## 🐛 Known Issues / Limitations

- Works best in **good lighting** conditions
- Currently supports **frontal face detection** only (Haar cascade)
- Recognition accuracy improves with more registered face samples
- Single camera (index `0`) supported by default

---

## 🔮 Future Improvements

- [ ] Add deep learning-based face detection (DNN / MTCNN)
- [ ] Export logs to CSV
- [ ] Multi-camera support
- [ ] Email/SMS alert on unknown face detection
- [ ] Face recognition accuracy graph/dashboard

---

## 👨‍💻 Author

**Ankit Kumar** — [@Kenk26](https://github.com/Kenk26)

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
