import cv2
import numpy as np
import pickle
import os
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog
from PIL import Image, ImageTk
import threading

class FaceRecognitionSecurity:
    def __init__(self):
        self.known_faces = {}
        self.data_file = "security_data.pkl"
        self.confidence_threshold = 60
        
        # Load face detection model
        self.face_detector = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        # Load face recognition model
        try:
            self.face_recognizer = cv2.face.LBPHFaceRecognizer_create()
            self.model_loaded = False
        except:
            self.face_recognizer = None
        
        self.load_data()
        
    def load_data(self):
        """Load previously registered faces"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'rb') as f:
                    data = pickle.load(f)
                    self.known_faces = data.get('faces', {})
                    
                if self.known_faces and self.face_recognizer:
                    self._train_recognizer()
            except Exception as e:
                print(f"Error loading data: {e}")
    
    def save_data(self):
        """Save registered faces to file"""
        try:
            data = {'faces': self.known_faces}
            with open(self.data_file, 'wb') as f:
                pickle.dump(data, f)
        except Exception as e:
            print(f"Error saving data: {e}")
    
    def _train_recognizer(self):
        """Train the face recognizer with registered faces"""
        if not self.face_recognizer or not self.known_faces:
            return
        
        faces = []
        labels = []
        label_map = {}
        
        for idx, (name, face_images) in enumerate(self.known_faces.items()):
            label_map[idx] = name
            for face_img in face_images:
                faces.append(face_img)
                labels.append(idx)
        
        if faces:
            self.face_recognizer.train(faces, np.array(labels))
            self.label_map = label_map
            self.model_loaded = True
    
    def log_access(self, name, granted, confidence=0):
        """Log access attempts"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = "GRANTED" if granted else "DENIED"
        conf_str = f"({confidence:.1f}%)" if confidence > 0 else ""
        log_entry = f"{timestamp} | {name} {conf_str} | {status}"
        
        with open("access_log.txt", "a") as f:
            f.write(log_entry + "\n")
        
        return log_entry
    
    def get_logs(self, last_n=20):
        """Get last N log entries"""
        if os.path.exists("access_log.txt"):
            with open("access_log.txt", "r") as f:
                logs = f.readlines()
                return [log.strip() for log in logs[-last_n:]]
        return []
    
    def delete_face(self, name):
        """Delete a registered face"""
        if name in self.known_faces:
            del self.known_faces[name]
            if self.known_faces:
                self._train_recognizer()
            else:
                self.model_loaded = False
            self.save_data()
            return True
        return False


class FaceRecognitionGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🛡️ Face Recognition Security System")
        self.root.geometry("1050x720")
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.root.geometry(f"1050x720+{250}+{25}")
        self.root.resizable(False, False)
        
        # Initialize security system
        self.security = FaceRecognitionSecurity()
        
        # Camera state
        self.camera = None
        self.camera_running = False
        self.monitoring_active = False
        
        # Registration state
        self.registration_mode = False
        self.registration_name = ""
        self.captured_faces = []
        self.max_captures = 50
        
        # Monitoring state
        self.frame_count = 0
        self.recognition_cooldown = {}
        
        # Setup GUI
        self.setup_styles()
        self.create_widgets()
        
        # Check for required libraries
        if not self.security.face_recognizer:
            messagebox.showerror("Error", 
                "opencv-contrib-python not installed!\n\n"
                "Please run: pip install opencv-contrib-python")
    
    def setup_styles(self):
        """Setup custom styles"""
        self.root.configure(bg='#1a1a2e')
        
        style = ttk.Style()
        style.theme_use('clam')
        
        # Modern color scheme
        bg_dark = '#1a1a2e'
        bg_card = '#16213e'
        accent = '#0f4c75'
        accent_light = '#3282b8'
        text_light = '#bbe1fa'
        success = '#00d9ff'
        danger = '#ff2e63'
        
        # Configure styles
        style.configure('Title.TLabel', font=('Segoe UI', 18, 'bold'), 
                       foreground=text_light, background=bg_dark)
        style.configure('Subtitle.TLabel', font=('Segoe UI', 10), 
                       foreground='#94a3b8', background=bg_card)
        style.configure('Status.TLabel', font=('Segoe UI', 11, 'bold'), 
                       foreground=success, background=bg_card)
        
        # Modern buttons
        style.configure('Action.TButton', 
                       font=('Segoe UI', 10, 'bold'),
                       padding=12,
                       relief='flat',
                       background=accent,
                       foreground=text_light,
                       borderwidth=0)
        style.map('Action.TButton',
                 background=[('active', accent_light), ('pressed', accent)])
        
        # Frame styles
        style.configure('Card.TFrame', background=bg_card, relief='flat')
        style.configure('Dark.TFrame', background=bg_dark)
        style.configure('Card.TLabelframe', 
                       background=bg_card, 
                       foreground=text_light,
                       borderwidth=0,
                       relief='flat')
        style.configure('Card.TLabelframe.Label', 
                       font=('Segoe UI', 10, 'bold'),
                       foreground=text_light,
                       background=bg_card)
    
    def create_widgets(self):
        """Create all GUI widgets"""
        # Main container with gradient effect
        main_container = ttk.Frame(self.root, padding="20", style='Dark.TFrame')
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Left panel - Camera view with modern card design
        left_panel = ttk.Frame(main_container, style='Card.TFrame', 
                              padding="20")
        left_panel.grid(row=0, column=0, padx=(0, 15), sticky=(tk.N, tk.S))
        
        # Camera title
        cam_title = ttk.Label(left_panel, text="🎥 Live Feed", 
                             font=('Segoe UI', 14, 'bold'),
                             foreground='#bbe1fa',
                             background='#16213e')
        cam_title.grid(row=0, column=0, pady=(0, 15))
        
        # Camera display with rounded effect
        camera_frame = tk.Frame(left_panel, bg='#0f4c75', 
                               highlightthickness=2,
                               highlightbackground='#3282b8')
        camera_frame.grid(row=1, column=0, pady=(0, 15))
        
        self.camera_label = tk.Label(camera_frame, bg='#0a1828')
        self.camera_label.pack(padx=3, pady=3)
        
        # Set default camera display
        default_img = Image.new('RGB', (640, 480), color='#0a1828')
        default_photo = ImageTk.PhotoImage(default_img)
        self.camera_label.configure(image=default_photo)
        self.camera_label.image = default_photo
        
        # Status label with icon
        status_frame = tk.Frame(left_panel, bg='#16213e')
        status_frame.grid(row=2, column=0)
        
        self.status_icon = ttk.Label(status_frame, text="⚫", 
                                     font=('Segoe UI', 12),
                                     background='#16213e')
        self.status_icon.pack(side=tk.LEFT, padx=(0, 8))
        
        self.status_label = ttk.Label(status_frame, text="Camera Offline", 
                                     font=('Segoe UI', 11, 'bold'),
                                     foreground='#94a3b8',
                                     background='#16213e')
        self.status_label.pack(side=tk.LEFT)
        
        # Right panel - Modern control panel
        right_panel = ttk.Frame(main_container, style='Dark.TFrame')
        right_panel.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Header section
        header_frame = ttk.Frame(right_panel, style='Dark.TFrame')
        header_frame.grid(row=0, column=0, pady=(0, 20), sticky=tk.W)
        
        title_label = ttk.Label(header_frame, 
                               text="🛡️ Security Hub",
                               style='Title.TLabel')
        title_label.grid(row=0, column=0, sticky=tk.W)
        
        subtitle_label = ttk.Label(header_frame,
                                  text="AI-Powered Face Recognition System",
                                  font=('Segoe UI', 9),
                                  foreground='#64748b',
                                  background='#1a1a2e')
        subtitle_label.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        
        # System info card with modern design
        info_card = ttk.LabelFrame(right_panel, text="📊 System Status", 
                                  style='Card.TLabelframe',
                                  padding="15")
        info_card.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        
        self.info_text = tk.Text(info_card, height=4, width=36, 
                                font=('Consolas', 9),
                                bg='#0a1828',
                                fg='#bbe1fa',
                                relief='flat',
                                borderwidth=0,
                                padx=10,
                                pady=8)
        self.info_text.grid(row=0, column=0)
        self.update_system_info()
        
        # Action buttons with modern styling
        btn_frame = ttk.Frame(right_panel, style='Dark.TFrame')
        btn_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        
        # Create modern buttons with custom styling
        buttons = [
            ("➕ Register New Face", self.start_registration, '#00d9ff'),
            ("🔒 Start Monitoring", self.start_monitoring, '#00d9ff'),
            ("⏹️  Stop Monitoring", self.stop_monitoring, '#ff2e63'),
            ("👥 Manage Faces", self.manage_faces, '#3282b8'),
            ("📋 View Access Logs", self.view_logs, '#3282b8')
        ]
        
        for i, (text, command, color) in enumerate(buttons):
            btn = tk.Button(btn_frame, text=text, command=command,
                          font=('Segoe UI', 10, 'bold'),
                          bg=color, fg='#ffffff',
                          activebackground=color,
                          activeforeground='#ffffff',
                          relief='flat',
                          cursor='hand2',
                          padx=20, pady=12,
                          borderwidth=0)
            btn.grid(row=i, column=0, sticky=(tk.W, tk.E), pady=4)
            
            # Hover effect
            def on_enter(e, btn=btn):
                btn['bg'] = self.lighten_color(btn['bg'])
            def on_leave(e, btn=btn, orig_color=color):
                btn['bg'] = orig_color
            
            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)
        
        # Access logs card with modern list
        logs_card = ttk.LabelFrame(right_panel, text="📋 Recent Access Logs", 
                                   style='Card.TLabelframe',
                                   padding="15")
        logs_card.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Custom listbox styling
        list_frame = tk.Frame(logs_card, bg='#0a1828')
        list_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        scrollbar = tk.Scrollbar(list_frame, bg='#16213e', 
                                troughcolor='#0a1828',
                                highlightthickness=0,
                                borderwidth=0)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.logs_listbox = tk.Listbox(list_frame, 
                                        height=12, 
                                        width=32,
                                        yscrollcommand=scrollbar.set,
                                        font=('Consolas', 8),
                                        bg='#0a1828',
                                        fg='#bbe1fa',
                                        selectbackground='#3282b8',
                                        selectforeground='#ffffff',
                                        relief='flat',
                                        borderwidth=0,
                                        highlightthickness=0)
        self.logs_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.logs_listbox.yview)
        
        self.update_logs_display()
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_container.rowconfigure(0, weight=1)
        right_panel.rowconfigure(3, weight=1)
        logs_card.rowconfigure(0, weight=1)
        logs_card.columnconfigure(0, weight=1)
        
        # Initialize logs display
        self.update_logs_display()
    
    def update_logs_display(self):
        """Update the access logs listbox"""
        self.logs_listbox.delete(0, tk.END)
        logs = self.security.get_logs(20)
        if logs:
            for log in reversed(logs):  # Show newest first
                # Format and color code
                if "GRANTED" in log:
                    self.logs_listbox.insert(tk.END, f"✓ {log}")
                else:
                    self.logs_listbox.insert(tk.END, f"✗ {log}")
        else:
            self.logs_listbox.insert(tk.END, "No access logs yet")
    
    def lighten_color(self, hex_color):
        """Lighten a hex color for hover effect"""
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        r = min(255, int(r * 1.2))
        g = min(255, int(g * 1.2))
        b = min(255, int(b * 1.2))
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def update_system_info(self):
        """Update system information display"""
        self.info_text.delete(1.0, tk.END)
        info = f"Registered Faces: {len(self.security.known_faces)}\n"
        info += f"Model Status: {'Trained' if self.security.model_loaded else 'Not Trained'}\n"
        info += f"Camera: {'ON' if self.camera_running else 'OFF'}\n"
        info += f"Monitoring: {'ACTIVE' if self.monitoring_active else 'INACTIVE'}"
        self.info_text.insert(1.0, info)
    
    def update_faces_list(self):
        """Update the registered faces listbox"""
        self.faces_listbox.delete(0, tk.END)
        for name, samples in self.security.known_faces.items():
            self.faces_listbox.insert(tk.END, 
                                     f"{name} ({len(samples)} samples)")
    
    def start_camera(self):
        """Start camera capture"""
        if not self.camera_running:
            self.camera = cv2.VideoCapture(0)
            self.camera_running = True
            self.update_camera()
    
    def stop_camera(self):
        """Stop camera capture"""
        self.camera_running = False
        if self.camera:
            self.camera.release()
            self.camera = None
        
        # Set blank/default image
        default_img = Image.new('RGB', (640, 480), color='#0a1828')
        default_photo = ImageTk.PhotoImage(default_img)
        self.camera_label.configure(image=default_photo)
        self.camera_label.image = default_photo
    
    def update_camera(self):
        """Update camera frame"""
        if not self.camera_running:
            return
        
        ret, frame = self.camera.read()
        if ret:
            # Flip frame first for mirror effect
            frame = cv2.flip(frame, 1)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Registration mode
            if self.registration_mode:
                faces = self.security.face_detector.detectMultiScale(
                    gray, scaleFactor=1.3, minNeighbors=5, minSize=(100, 100)
                )
                
                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                
                info = f"Captured: {len(self.captured_faces)}/{self.max_captures}"
                cv2.putText(frame, info, (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Auto-capture
                if len(faces) == 1 and len(self.captured_faces) < self.max_captures:
                    x, y, w, h = faces[0]
                    face_roi = gray[y:y+h, x:x+w]
                    face_roi = cv2.resize(face_roi, (200, 200))
                    self.captured_faces.append(face_roi)
                    
                    if len(self.captured_faces) >= self.max_captures:
                        self.complete_registration()
                elif len(faces) > 1:
                    cv2.putText(frame, "Multiple faces detected!", 
                               (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 
                               0.6, (0, 0, 255), 2)
            
            # Monitoring mode
            elif self.monitoring_active and self.security.model_loaded:
                self.frame_count += 1
                faces = self.security.face_detector.detectMultiScale(
                    gray, scaleFactor=1.3, minNeighbors=5, minSize=(100, 100)
                )
                
                for (x, y, w, h) in faces:
                    face_roi = gray[y:y+h, x:x+w]
                    face_roi = cv2.resize(face_roi, (200, 200))
                    
                    label, confidence = self.security.face_recognizer.predict(face_roi)
                    confidence_percent = 100 - min(confidence, 100)
                    
                    if confidence < 50:  # Stricter threshold
                        name = self.security.label_map[label]
                        color = (0, 255, 0)
                        confidence_percent = max(0, 100 - confidence)  # Fix percentage calculation
                        
                        if name not in self.recognition_cooldown or \
                        self.frame_count - self.recognition_cooldown[name] > 30:
                            log_entry = self.security.log_access(name, True, confidence_percent)
                            self.recognition_cooldown[name] = self.frame_count
                            self.update_logs_display()
                    else:
                        name = "Unknown"
                        color = (0, 0, 255)
                        confidence_percent = 0
                        
                        if "Unknown" not in self.recognition_cooldown or \
                        self.frame_count - self.recognition_cooldown["Unknown"] > 30:
                            self.security.log_access("Unknown Person", False, 0)  # Add confidence parameter
                            self.recognition_cooldown["Unknown"] = self.frame_count
                            self.update_logs_display()
                                        
                    cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
                    cv2.rectangle(frame, (x, y+h-35), (x+w, y+h), color, cv2.FILLED)
                    text = f"{name} ({confidence_percent:.0f}%)"
                    cv2.putText(frame, text, (x+6, y+h-6),
                    cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)
                
                status = f"MONITORING | Registered: {len(self.security.known_faces)}"
                cv2.putText(frame, status, (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # Convert and display
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (640, 480))
            image = Image.fromarray(frame)
            photo = ImageTk.PhotoImage(image=image)
            self.camera_label.configure(image=photo)
            self.camera_label.image = photo
        
        if self.camera_running:
            self.root.after(10, self.update_camera)
    
    def start_registration(self):
        """Start face registration process"""
        # Create custom dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Register New Face")
        dialog.geometry("450x200")
        dialog.configure(bg='#1a1a2e')
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (450 // 2)
        y = (dialog.winfo_screenheight() // 2) - (200 // 2)
        dialog.geometry(f'450x200+{x}+{y}')
        
        # Header
        header = tk.Frame(dialog, bg='#16213e', height=60)
        header.pack(fill=tk.X)
        
        title = tk.Label(header, text="👤 Register New Face", 
                        font=('Segoe UI', 14, 'bold'),
                        fg='#bbe1fa', bg='#16213e')
        title.pack(pady=15)
        
        # Content frame
        content = tk.Frame(dialog, bg='#1a1a2e')
        content.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)
        
        # Label
        label = tk.Label(content, text="Enter name for registration:", 
                        font=('Segoe UI', 11),
                        fg='#bbe1fa', bg='#1a1a2e')
        label.pack(pady=(10, 10))
        
        # Entry field
        entry = tk.Entry(content, 
                        font=('Segoe UI', 12),
                        bg='#0a1828',
                        fg='#bbe1fa',
                        insertbackground='#00d9ff',
                        relief='flat',
                        borderwidth=2,
                        highlightthickness=2,
                        highlightbackground='#3282b8',
                        highlightcolor='#00d9ff')
        entry.pack(fill=tk.X, pady=(0, 20), ipady=8)
        entry.focus_set()
        
        # Button frame
        btn_frame = tk.Frame(content, bg='#1a1a2e')
        btn_frame.pack()
        
        result = {'name': None}
        
        def on_ok():
            name = entry.get().strip()
            if name:
                result['name'] = name
                dialog.destroy()
            else:
                messagebox.showwarning("Invalid Input", "Please enter a valid name!")
        
        def on_cancel():
            dialog.destroy()
        
        # OK button
        ok_btn = tk.Button(btn_frame, text="✓  OK", 
                          command=on_ok,
                          font=('Segoe UI', 10, 'bold'),
                          bg='#00d9ff', fg='#ffffff',
                          activebackground='#33e5ff',
                          activeforeground='#ffffff',
                          relief='flat',
                          cursor='hand2',
                          padx=30, pady=10,
                          borderwidth=0)
        ok_btn.pack(side=tk.LEFT, padx=5)
        
        # Cancel button
        cancel_btn = tk.Button(btn_frame, text="✕  Cancel", 
                              command=on_cancel,
                              font=('Segoe UI', 10, 'bold'),
                              bg='#3282b8', fg='#ffffff',
                              activebackground='#4a9dcc',
                              activeforeground='#ffffff',
                              relief='flat',
                              cursor='hand2',
                              padx=30, pady=10,
                              borderwidth=0)
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        # Bind Enter key to OK
        entry.bind('<Return>', lambda e: on_ok())
        
        # Wait for dialog to close
        self.root.wait_window(dialog)
        
        # Process the result
        if result['name']:
            self.registration_name = result['name']
            self.registration_mode = True
            self.captured_faces = []
            self.start_camera()
            self.status_label.config(text="Registering...", foreground='#00d9ff')
            self.status_icon.config(text="🔴", foreground='#ff2e63')
            self.update_system_info()
    
    # NEW
    def complete_registration(self):
        """Complete the registration process"""
        self.registration_mode = False
        self.camera_running = False  # Stop the camera loop immediately
        
        if len(self.captured_faces) >= 3:
            self.security.known_faces[self.registration_name] = self.captured_faces
            self.security._train_recognizer()
            self.security.save_data()
            
            # Use after() to stop camera and show message after current frame
            self.root.after(100, lambda: self._finish_registration(True))
        else:
            self.root.after(100, lambda: self._finish_registration(False))

    def _finish_registration(self, success):
        """Finish registration after camera has stopped"""
        self.stop_camera()
        self.status_label.config(text="Camera Offline", foreground='#94a3b8')
        self.status_icon.config(text="⚫", foreground='#94a3b8')
        
        if success:
            messagebox.showinfo("Success", 
                f"Successfully registered {self.registration_name}!\n"
                f"Captured {len(self.captured_faces)} samples.")
        else:
            messagebox.showerror("Failed", 
                f"Registration failed! Only captured {len(self.captured_faces)} samples.\n"
                "Need at least 3 samples.")
        
        self.update_system_info()
        
    
    def start_monitoring(self):
        """Start security monitoring"""
        if not self.security.known_faces:
            messagebox.showwarning("No Faces Registered", 
                "Please register faces before starting monitoring!")
            return
        
        if not self.security.model_loaded:
            messagebox.showwarning("Model Not Trained", 
                "Please register faces first!")
            return
        
        self.monitoring_active = True
        self.frame_count = 0
        self.recognition_cooldown = {}
        self.start_camera()
        self.status_label.config(text="MONITORING ACTIVE", foreground='#00d9ff')
        self.status_icon.config(text="🟢", foreground='#00d9ff')
        self.update_system_info()
    
    def stop_monitoring(self):
        """Stop security monitoring"""
        self.monitoring_active = False
        self.stop_camera()
        self.status_label.config(text="Camera Offline", foreground='#94a3b8')
        self.status_icon.config(text="⚫", foreground='#94a3b8')
        self.update_system_info()
    
    def manage_faces(self):
        """Open face management window"""
        if not self.security.known_faces:
            messagebox.showinfo("No Faces", "No registered faces to manage!")
            return
        
        manage_window = tk.Toplevel(self.root)
        manage_window.title("🗑️ Manage Registered Faces")
        manage_window.geometry("450x350")
        manage_window.configure(bg='#1a1a2e')
        
        # Header
        header = tk.Frame(manage_window, bg='#16213e', height=60)
        header.pack(fill=tk.X, pady=(0, 20))
        
        title = tk.Label(header, text="Delete Registered User", 
                        font=('Segoe UI', 14, 'bold'),
                        fg='#bbe1fa', bg='#16213e')
        title.pack(pady=15)
        
        # Listbox frame
        list_frame = tk.Frame(manage_window, bg='#16213e')
        list_frame.pack(padx=20, fill=tk.BOTH, expand=True)
        
        listbox = tk.Listbox(list_frame, height=10, 
                           font=('Consolas', 10),
                           bg='#0a1828',
                           fg='#bbe1fa',
                           selectbackground='#3282b8',
                           selectforeground='#ffffff',
                           relief='flat',
                           borderwidth=0)
        listbox.pack(padx=15, pady=15, fill=tk.BOTH, expand=True)
        
        for name, samples in self.security.known_faces.items():
            listbox.insert(tk.END, f"👤 {name} ({len(samples)} samples)")
        
        def delete_selected():
            selection = listbox.curselection()
            if selection:
                name = listbox.get(selection[0]).split(' (')[0].replace('👤 ', '')
                result = messagebox.askyesno("Confirm Delete", 
                    f"Are you sure you want to delete {name}?")
                if result:
                    self.security.delete_face(name)
                    self.update_system_info()
                    manage_window.destroy()
                    messagebox.showinfo("Success", f"✓ Deleted {name} from system!")
        
        # Delete button
        btn = tk.Button(manage_window, text="🗑️  Delete Selected", 
                       command=delete_selected,
                       font=('Segoe UI', 10, 'bold'),
                       bg='#ff2e63', fg='#ffffff',
                       activebackground='#ff4976',
                       activeforeground='#ffffff',
                       relief='flat',
                       cursor='hand2',
                       padx=30, pady=12,
                       borderwidth=0)
        btn.pack(pady=20)
    
    def view_logs(self):
        """Open logs viewer window"""
        logs_window = tk.Toplevel(self.root)
        logs_window.title("📋 Access Logs")
        logs_window.geometry("750x450")
        logs_window.configure(bg='#1a1a2e')
        
        # Header
        header = tk.Frame(logs_window, bg='#16213e', height=60)
        header.pack(fill=tk.X, pady=(0, 20))
        
        title = tk.Label(header, text="Recent Access Logs", 
                        font=('Segoe UI', 14, 'bold'),
                        fg='#bbe1fa', bg='#16213e')
        title.pack(side=tk.LEFT, padx=20, pady=15)
        
        subtitle = tk.Label(header, text="Last 50 entries", 
                           font=('Segoe UI', 9),
                           fg='#64748b', bg='#16213e')
        subtitle.pack(side=tk.LEFT, pady=15)
        
        # Text area
        text_frame = tk.Frame(logs_window, bg='#16213e')
        text_frame.pack(padx=20, pady=(0, 20), fill=tk.BOTH, expand=True)
        
        text_area = scrolledtext.ScrolledText(text_frame, 
                                             font=('Consolas', 9),
                                             width=85, height=20,
                                             bg='#0a1828',
                                             fg='#bbe1fa',
                                             relief='flat',
                                             borderwidth=0,
                                             padx=15,
                                             pady=15)
        text_area.pack(fill=tk.BOTH, expand=True)
        
        logs = self.security.get_logs(50)
        if logs:
            for log in logs:
                # Color code logs
                if "GRANTED" in log:
                    text_area.insert(tk.END, log + "\n")
                else:
                    text_area.insert(tk.END, log + "\n")
        else:
            text_area.insert(tk.END, "No logs available")
        
        text_area.config(state=tk.DISABLED)
        
        # Close button
        btn = tk.Button(logs_window, text="✕  Close", 
                       command=logs_window.destroy,
                       font=('Segoe UI', 10, 'bold'),
                       bg='#3282b8', fg='#ffffff',
                       activebackground='#4a9dcc',
                       activeforeground='#ffffff',
                       relief='flat',
                       cursor='hand2',
                       padx=30, pady=12,
                       borderwidth=0)
        btn.pack(pady=(0, 20))
    
    def on_closing(self):
        """Handle window closing"""
        self.stop_camera()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = FaceRecognitionGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()