import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import signal
from scipy.io import loadmat

def process_ecg(file_path, file_type, output_dir):
    if file_type == "csv":
        df = pd.read_csv(file_path, header=None)
        if isinstance(df.iloc[0, 0], str):
            # Skip header lines if present in CSV
            df = pd.read_csv(file_path, skiprows=2, header=None)
        time = df.iloc[:, 0].values
        ecg = df.iloc[:, 1].values
        fs = 1 / (time[1] - time[0])
    elif file_type == "mat":
        data = loadmat(file_path)
        ecg = data["data"][:, 0]
        isi = float(data["isi"]) / 1000
        fs = 1 / isi
        time = np.linspace(0, len(ecg) / fs, num=len(ecg))
    else:
        raise ValueError("Invalid file type")

    # Save original ECG plot (for comparison toggle)
    raw_img = os.path.join(output_dir, "original_raw.png")
    plt.figure(dpi=300, figsize=(10, 4))
    plt.plot(time, ecg, label="Original ECG", color="orange")
    plt.title("Original ECG")
    plt.xlabel("Time (s)")
    plt.ylabel("Amplitude")
    plt.grid()
    plt.tight_layout()
    plt.savefig(raw_img)
    plt.close()

    # Baseline removal (high-pass filter at 0.5 Hz)
    b, a = signal.butter(4, 0.5 / (fs / 2), btype='high')
    ecg_filtered = signal.filtfilt(b, a, ecg)

    # R-peak detection
    threshold = 0.5 * np.max(ecg_filtered)
    distance = int(0.25 * fs)  # min distance between peaks ~0.25s
    peaks, _ = signal.find_peaks(ecg_filtered, height=threshold, distance=distance)
    heart_rate = round(len(peaks) / ((time[-1] - time[0]) / 60), 2)

    # Save plots of baseline-corrected signal and R-peak detection
    baseline_img = os.path.join(output_dir, "baseline_corrected.png")
    rpeak_img = os.path.join(output_dir, "rpeak_detected.png")

    plt.figure(dpi=300, figsize=(10, 4))
    plt.plot(time, ecg_filtered, label="Filtered ECG", color="navy")
    plt.title("Baseline Corrected ECG")
    plt.xlabel("Time (s)")
    plt.ylabel("Amplitude")
    plt.grid()
    plt.tight_layout()
    plt.savefig(baseline_img)
    plt.close()

    plt.figure(dpi=300, figsize=(10, 4))
    plt.plot(time, ecg_filtered, label="Filtered ECG", color="teal")
    plt.plot(time[peaks], ecg_filtered[peaks], "ro", label="R-peaks")
    plt.title("R-peak Detection")
    plt.xlabel("Time (s)")
    plt.ylabel("Amplitude")
    plt.legend()
    plt.grid()
    plt.tight_layout()
    plt.savefig(rpeak_img)
    plt.close()

    ecg_points = ecg.tolist()[:300]  # limit to first 300 points for preview
    return {
        "heart_rate": heart_rate,
        "num_beats": len(peaks),
        "baseline_plot": f"uploads/{os.path.basename(output_dir)}/baseline_corrected.png",
        "rpeak_plot": f"uploads/{os.path.basename(output_dir)}/rpeak_detected.png",
        "raw_plot": f"uploads/{os.path.basename(output_dir)}/original_raw.png",
        "ecg_points": ecg_points  # NEW
    }

def analyze_ecg(file_path, file_type):
    """
    Load and filter ECG data, then detect R-peaks without generating plots.
    Returns (time, ecg_filtered, peaks, fs).
    """
    if file_type == "csv":
        try:
            df = pd.read_csv(file_path, header=None, encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, header=None, encoding='ISO-8859-1')  # fallback
        if isinstance(df.iloc[0, 0], str):
            df = pd.read_csv(file_path, skiprows=2, header=None)
        time = df.iloc[:, 0].values
        ecg = df.iloc[:, 1].values
        fs = 1 / (time[1] - time[0])
    elif file_type == "mat":
        data = loadmat(file_path)
        ecg = data["data"][:, 0]
        isi = float(data["isi"]) / 1000
        fs = 1 / isi
        time = np.linspace(0, len(ecg) / fs, num=len(ecg))
    else:
        raise ValueError("Invalid file type")
    # Apply same baseline removal filter as process_ecg
    b, a = signal.butter(4, 0.5 / (fs / 2), btype='high')
    ecg_filtered = signal.filtfilt(b, a, ecg)
    # Detect peaks in filtered signal
    threshold = 0.5 * np.max(ecg_filtered)
    distance = int(0.25 * fs)
    peaks, _ = signal.find_peaks(ecg_filtered, height=threshold, distance=distance)
    return time, ecg_filtered, peaks, fs
