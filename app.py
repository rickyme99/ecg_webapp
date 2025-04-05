import os
import sqlite3
from flask import Flask, request, redirect, url_for, render_template, session, flash
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from fpdf import FPDF
import pandas as pd
from flask import send_file
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "super_secret_key"
DATABASE = "database.db"

def init_db():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()

    # Users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    # ✅ Add this for uploads
    cur.execute("""
        CREATE TABLE IF NOT EXISTS uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            filename TEXT,
            upload_date TEXT,
            result_path TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


@app.route("/")
def home():
    # Home page rendering (no change from original)
    return render_template("home.html")

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash("Please login to view your profile.")
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, filename, upload_date, result_path FROM uploads WHERE user_id = ?', (user_id,))
    uploads = cursor.fetchall()
    conn.close()

    return render_template('profile.html', uploads=uploads)

@app.route('/upload_only', methods=['POST'])
def upload_only():
    if "user_id" not in session:
        return redirect(url_for('login'))

    username = session.get("username")
    file = request.files.get("ecgfile")
    if not file or file.filename == "":
        flash("No file selected.", "warning")
        return redirect(url_for('profile'))

    filename = secure_filename(file.filename)
    user_folder = os.path.join(app.root_path, 'static', 'uploads', username)
    if not os.path.exists(user_folder):
        os.makedirs(user_folder, exist_ok=True)

    filepath = os.path.join(user_folder, filename)
    file.save(filepath)

    upload_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    result_path = os.path.join('static', 'uploads', username, 'rpeak_detected.png')  # placeholder

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO uploads (user_id, filename, upload_date, result_path)
        VALUES (?, ?, ?, ?)
    ''', (session['user_id'], filename, upload_date, result_path))
    conn.commit()
    conn.close()

    flash("File uploaded successfully.", "success")
    return redirect(url_for('profile'))

@app.route('/analyze/<int:upload_id>', methods=['POST'])
def analyze_file(upload_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT filename FROM uploads WHERE id = ? AND user_id = ?', (upload_id, session['user_id']))
    row = cursor.fetchone()
    conn.close()

    if not row:
        flash("File not found.", "danger")
        return redirect(url_for('profile'))

    filename = row[0]
    username = session['username']
    user_folder = os.path.join(app.root_path, 'static', 'uploads', username)
    file_path = os.path.join(user_folder, filename)
    file_type = filename.split('.')[-1].lower()

    from ecg_processing import process_ecg
    result = process_ecg(file_path, file_type, user_folder)

    # Save result in session
    session['last_file_path'] = file_path
    session['last_filetype'] = file_type

    ecg_data_for_chart = result["ecg_points"]

    return render_template("upload.html", username=username, processed=True,
                           heart_rate=result["heart_rate"], num_beats=result["num_beats"],
                           baseline_plot=result["baseline_plot"],
                           rpeak_plot=result["rpeak_plot"],
                           raw_plot=result["raw_plot"],
                           ecg_data=ecg_data_for_chart)

@app.route('/delete_upload/<int:upload_id>', methods=['POST'])
def delete_upload(upload_id):
    if 'user_id' not in session:
        flash("You must be logged in to delete files.")
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM uploads WHERE id = ? AND user_id = ?', (upload_id, session['user_id']))
    conn.commit()
    conn.close()

    flash("Upload deleted successfully.")
    return redirect(url_for('profile'))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        # Attempt to create new user
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cur.fetchone():
            flash("Username already exists.", "danger")
        else:
            try:
                password_hash = generate_password_hash(password)
                cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password_hash))
                conn.commit()
                flash("Account created successfully. Please log in.", "success")
                return redirect(url_for('login'))
            except Exception as e:
                flash("Error creating account.", "danger")
        conn.close()
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        cur.execute("SELECT id, password FROM users WHERE username = ?", (username,))
        user = cur.fetchone()
        conn.close()
        if user and check_password_hash(user[1], password):
            # Successful login
            session["user_id"] = user[0]
            session["username"] = username
            flash("Logged in successfully.", "success")
            return redirect(url_for('profile'))
        else:
            flash("Invalid credentials.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for('login'))

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if "user_id" not in session:
        return redirect(url_for('login'))

    username = session.get("username", None)

    if request.method == "POST":
        # Handle file upload
        file = request.files.get("ecgfile")
        filetype = request.form.get("filetype")

        if not file or file.filename == "":
            flash("No file selected.", "warning")
            return redirect(url_for('upload'))

        filename = secure_filename(file.filename)
        user_folder = os.path.join(app.root_path, 'static', 'uploads', username)
        if not os.path.exists(user_folder):
            os.makedirs(user_folder, exist_ok=True)

        filepath = os.path.join(user_folder, filename)
        file.save(filepath)

        # ✅ Process ECG signal (baseline removal and R-peak detection)
        from ecg_processing import process_ecg
        result = process_ecg(filepath, filetype, user_folder)

        # ✅ Store for chart rendering or further session use
        ecg_data_for_chart = result["ecg_points"]
        session['last_file_path'] = filepath
        session['last_filetype'] = filetype

        # ✅ Save upload info to database
        user_id = session.get('user_id')
        upload_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        result_path = os.path.join('static', 'uploads', username, result["rpeak_plot"])

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO uploads (user_id, filename, upload_date, result_path)
            VALUES (?, ?, ?, ?)
        ''', (user_id, filename, upload_date, result_path))
        conn.commit()
        conn.close()

        return render_template("upload.html", username=username, processed=True,
                               heart_rate=result["heart_rate"], num_beats=result["num_beats"],
                               baseline_plot=result["baseline_plot"],
                               rpeak_plot=result["rpeak_plot"],
                               raw_plot=result["raw_plot"],
                               ecg_data=ecg_data_for_chart)

    # GET request – show upload page
    return render_template("upload.html", username=username)


@app.route("/advanced", methods=["POST"])
def advanced():
    # Route to handle advanced feature analysis after initial processing
    if 'user_id' not in session:
        return redirect(url_for('login'))
    username = session.get('username', None)
    user_folder = os.path.join(app.root_path, 'static', 'uploads', username)
    if not os.path.exists(user_folder):
        os.makedirs(user_folder, exist_ok=True)
    features = request.form.getlist('features')  # list of selected feature options
    file_path = session.get('last_file_path')
    file_type = session.get('last_filetype')
    if not file_path or not file_type:
        flash("No ECG file available for analysis. Please upload a file first.", "warning")
        return redirect(url_for('upload'))
    # Perform selected analyses
    from ecg_processing import analyze_ecg, process_ecg
    import numpy as np
    import matplotlib.pyplot as plt
    # Recompute or retrieve filtered signal and peaks
    time, ecg_filtered, peaks, fs = analyze_ecg(file_path, file_type)
    metrics = None
    rr_hist_rel = None
    if 'hrv' in features:
        if len(peaks) > 1:
            # Calculate HRV time-domain metrics
            rr_intervals = np.diff(time[peaks])
            sdnn = np.std(rr_intervals, ddof=1) * 1000.0        # SDNN in ms
            diff_rr = np.diff(rr_intervals)
            rmssd = np.sqrt(np.mean(diff_rr**2)) * 1000.0 if len(diff_rr) > 0 else 0.0  # RMSSD in ms
            nn50 = int(np.sum(np.abs(diff_rr) > 0.05))         # count of diff > 50ms
            pnn50 = (nn50 / len(diff_rr) * 100.0) if len(diff_rr) > 0 else 0.0  # pNN50 in %
            metrics = {
                "SDNN": round(sdnn, 2),
                "RMSSD": round(rmssd, 2),
                "pNN50": round(pnn50, 2),
                "NN50": nn50
            }
            session['metrics'] = metrics
    if 'hist' in features:
        rr_intervals = np.diff(time[peaks]) if len(peaks) > 1 else []
        if len(rr_intervals) > 1:
            # Plot and save RR-interval histogram
            hist_path = os.path.join(user_folder, 'rr_histogram.png')
            plt.figure(dpi=300, figsize=(6, 4))
            plt.hist(rr_intervals * 1000.0, bins=20, color='skyblue', edgecolor='black')
            plt.title('RR Interval Histogram')
            plt.xlabel('RR interval (ms)')
            plt.ylabel('Count')
            plt.tight_layout()
            plt.savefig(hist_path)
            plt.close()
            rr_hist_rel = f"uploads/{username}/rr_histogram.png"
    # Reuse the existing results for baseline and R-peak plots (no need to re-run analysis fully)
    result = process_ecg(file_path, file_type, user_folder)
    return render_template('upload.html', username=username, processed=True,
                           heart_rate=result['heart_rate'], num_beats=result['num_beats'],
                           baseline_plot=result['baseline_plot'], rpeak_plot=result['rpeak_plot'],
                           raw_plot=result['raw_plot'],
                           metrics=metrics, rr_hist_plot=rr_hist_rel)
@app.route("/export/<format>")
def export(format):
    metrics = session.get('metrics', {})
    username = session.get('username', 'user')
    filename = f"{username}_ecg_metrics"

    if format == "pdf":
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'ECG Analysis Metrics', ln=1, align='C')
        pdf.ln(10)
        pdf.set_font('Arial', '', 12)
        for k, v in metrics.items():
            pdf.cell(0, 10, f"{k}: {v}", ln=1)
        filepath = f"static/{filename}.pdf"
        pdf.output(filepath)
        return send_file(filepath, as_attachment=True)

    elif format == "excel":
        df = pd.DataFrame([metrics])
        filepath = f"static/{filename}.xlsx"
        df.to_excel(filepath, index=False)
        return send_file(filepath, as_attachment=True)

    return "Unsupported format", 400

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
