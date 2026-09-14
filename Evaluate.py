import os
import pandas as pd
import numpy as np
from sklearn.metrics import (accuracy_score, roc_auc_score, log_loss, 
                            roc_curve, precision_recall_curve, auc, brier_score_loss)
from sklearn.calibration import calibration_curve
from sklearn.metrics import confusion_matrix
import matplotlib.pyplot as plt
from LogisticRegression import parseData, row_to_features, model, possibleChamps
from sklearn.metrics import roc_curve, precision_recall_curve, auc


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(BASE_DIR, "data", "testing.csv")

n = len(possibleChamps)

df_test = pd.read_csv(data_path)

# Create parsed columns for t1, t2 and bans
df_test["t1"]   = df_test["team1_champions"].apply(parseData)
df_test["t2"]   = df_test["team2_champions"].apply(parseData)
df_test["bans"] = df_test["bans"].apply(parseData)

#Build the labeled vector. 1 if Team1 won, 0 otherwise
y_test = (df_test["winner"].str.strip().str.lower() == "team1").astype(int).values

X_test = np.vstack([
    row_to_features(t1, t2, b)
    for t1, t2, b in zip(df_test["t1"], df_test["t2"], df_test["bans"])
])

y_proba = model.predict_proba(X_test)[:, 1]
y_pred  = (y_proba >= 0.5).astype(int)

print("TEST Accuracy:", accuracy_score(y_test, y_pred))
print("TEST AUC:", roc_auc_score(y_test, y_proba))
print("TEST Log-loss:", log_loss(y_test, y_proba))

#Visualization
plt.hist(y_proba[y_test == 1], bins=30, alpha=0.7, label="Wins")
plt.hist(y_proba[y_test == 0], bins=30, alpha=0.7, label="Losses")
plt.xlabel("Predicted win probability")
plt.ylabel("Count")
plt.legend()
plt.title("Probability distribution on TEST data")
plt.show()

#ROC Curve and Precision-Recall Curve
fpr, tpr, _ = roc_curve(y_test, y_proba)
rocAuc = auc(fpr, tpr)

plt.figure(figsize=(6, 5))
plt.plot(fpr, tpr, label=f"ROC curve (AUC = {rocAuc:.3f})")
plt.plot([0, 1], [0, 1], linestyle="--", label="Random")
plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title("ROC Curve")
plt.legend()
plt.grid(True)
plt.show()

#Precision–Recall curve
precision, recall, _ = precision_recall_curve(y_test, y_proba)
prAuc = auc(recall, precision)

plt.figure(figsize=(6, 5))
plt.plot(recall, precision, label=f"PR curve (AUC = {prAuc:.3f})")
plt.xlabel("Recall")
plt.ylabel("Precision")
plt.title("Precision - Recall Curve")
plt.legend()
plt.grid(True)
plt.show()

#Reliability Diagram
probTrue, probPred = calibration_curve(y_test, y_proba, n_bins=10, strategy="uniform")
brier = brier_score_loss(y_test, y_proba)

plt.figure(figsize=(6, 5))
plt.plot(probPred, probTrue, marker="o", label="Model")
plt.plot([0, 1], [0, 1], linestyle="--", label="Perfectly calibrated")
plt.xlabel("Predicted probability")
plt.ylabel("Observed win rate")
plt.title(f"Calibration plot (Brier score = {brier:.3f})")
plt.legend()
plt.grid(True)
plt.show()

#Confusion Matrix
cm = confusion_matrix(y_test, y_pred)
labels = ["Loss", "Win"]

fig, ax = plt.subplots(figsize=(4, 4))
im = ax.imshow(cm, cmap="Blues")

ax.set_xticks([0, 1])
ax.set_yticks([0, 1])
ax.set_xticklabels(labels)
ax.set_yticklabels(labels)
ax.set_xlabel("Predicted")
ax.set_ylabel("Actual")
ax.set_title("Confusion Matrix")

#Annotate each cell with the count
for i in range(2):
    for j in range(2):
        ax.text(j, i, cm[i, j], ha="center", va="center", color="black")

plt.colorbar(im, ax=ax)
plt.tight_layout()
plt.show()
