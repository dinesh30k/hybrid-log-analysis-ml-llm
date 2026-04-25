import pickle
import sys
import re

# -------------------------------
# SAME CLEANING AS TRAINING
# -------------------------------
def clean_log(text):
    text = text.lower()
    text = re.sub(r'\d+', '', text)
    text = re.sub(r'[^a-z\s]', '', text)
    return text.strip()

# -------------------------------
# LOAD MODEL + VECTORIZER
# -------------------------------
model = pickle.load(open("../ml-api/model.pkl", "rb"))
vectorizer = pickle.load(open("../ml-api/vectorizer.pkl", "rb"))

# -------------------------------
# PREDICTION FUNCTION
# -------------------------------
def predict_log(log_text):
    cleaned = clean_log(log_text)   # 🔥 IMPORTANT
    log_vector = vectorizer.transform([cleaned])
    prediction = model.predict(log_vector)[0]
    return prediction

# -------------------------------
# CLI TEST
# -------------------------------
if __name__ == "__main__":
    log = sys.argv[1]
    result = predict_log(log)
    print(result)