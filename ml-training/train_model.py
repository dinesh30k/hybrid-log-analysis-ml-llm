import pandas as pd
import re
import pickle

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score

def clean_log(text):
    text = text.lower()
    text = re.sub(r'\d+', '', text)
    text = re.sub(r'[^a-z\s]', '', text)
    return text.strip()


df = pd.read_csv("logs_dataset.csv")

print("Dataset Loaded ✅")
print(df.head())


df["cleaned"] = df["Content"].apply(clean_log)

X = df["cleaned"]
y = df["Level"]

print("\nLabel Distribution:")
print(y.value_counts())


X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)


vectorizer = TfidfVectorizer(
    max_features=5000,
    ngram_range=(1, 2)  # big improvement 🔥
)

X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)


model = LogisticRegression(max_iter=1000)

model.fit(X_train_vec, y_train)

y_pred = model.predict(X_test_vec)

print("\nModel Evaluation 🔍")
print("Accuracy:", accuracy_score(y_test, y_pred))

print("\nClassification Report:\n")
print(classification_report(y_test, y_pred))


with open("../ml-api/model.pkl", "wb") as f:
    pickle.dump(model, f)

with open("../ml-api/vectorizer.pkl", "wb") as f:
    pickle.dump(vectorizer, f)

print("\n✅ Model & Vectorizer saved successfully!")


print("\n🔎 Real-world test:")

samples = [
    "disk completely failed and crashed",
    "ssl certificate not trusted connection failed",
    "low memory warning in system",
    "block received successfully",
    "unauthorized access detected"
]

for s in samples:
    cleaned = clean_log(s)
    vec = vectorizer.transform([cleaned])
    pred = model.predict(vec)[0]
    print(f"{s} → {pred}")