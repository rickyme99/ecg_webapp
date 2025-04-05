import matplotlib.pyplot as plt
import numpy as np

# Data for 5 folds (values taken from the table)
folds = np.array([1, 2, 3, 4, 5])

# Metrics for Normal and Symptom categories
prec_normal   = np.array([86.79, 83.93, 82.82, 94.11, 92.45])
prec_symptom  = np.array([93.55, 94.92, 91.67, 96.88, 98.39])

rec_normal    = np.array([92, 94, 90, 96, 98])
rec_symptom   = np.array([89.23, 86.20, 84.62, 95.38, 93.85])

f1_normal     = np.array([89.31, 88.68, 86.26, 95.05, 95.14])
f1_symptom    = np.array([91.34, 90.02, 88.00, 96.12, 96.07])

# Accuracy is available only for the Normal rows per fold
acc_normal    = np.array([90.43, 89.57, 86.96, 95.65, 95.65])

# Create a 2x2 grid for subplots
fig, axs = plt.subplots(2, 2, figsize=(12, 10))
width = 0.35  # Width of each bar
x = np.arange(len(folds))  # X positions for the groups

# --- Precision subplot ---
ax = axs[0, 0]
ax.bar(x - width/2, prec_normal, width, label='Normal')
ax.bar(x + width/2, prec_symptom, width, label='Symptom')
ax.set_xticks(x)
ax.set_xticklabels(folds)
ax.set_xlabel('Fold')
ax.set_ylabel('Precision (%)')
ax.set_title('Precision per Fold')
ax.legend()

# --- Recall subplot ---
ax = axs[0, 1]
ax.bar(x - width/2, rec_normal, width, label='Normal')
ax.bar(x + width/2, rec_symptom, width, label='Symptom')
ax.set_xticks(x)
ax.set_xticklabels(folds)
ax.set_xlabel('Fold')
ax.set_ylabel('Recall (%)')
ax.set_title('Recall per Fold')
ax.legend()

# --- F1 Score subplot ---
ax = axs[1, 0]
ax.bar(x - width/2, f1_normal, width, label='Normal')
ax.bar(x + width/2, f1_symptom, width, label='Symptom')
ax.set_xticks(x)
ax.set_xticklabels(folds)
ax.set_xlabel('Fold')
ax.set_ylabel('F1 Score (%)')
ax.set_title('F1 Score per Fold')
ax.legend()

# --- Accuracy subplot (only Normal) ---
ax = axs[1, 1]
ax.bar(x, acc_normal, width, label='Normal', color='skyblue', edgecolor='black')
ax.set_xticks(x)
ax.set_xticklabels(folds)
ax.set_xlabel('Fold')
ax.set_ylabel('Accuracy (%)')
ax.set_title('Accuracy per Fold (Normal)')
ax.legend()

plt.tight_layout()
plt.show()
