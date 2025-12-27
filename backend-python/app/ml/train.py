
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import confusion_matrix, f1_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

# Determine paths relative to this script
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODELS_DIR = os.path.join(BASE_DIR, "models")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

def load_data():
    records = []
    # Load all JSONs in data directory
    if os.path.exists(DATA_DIR):
        for filename in os.listdir(DATA_DIR):
            if filename.endswith(".json"):
                path = os.path.join(DATA_DIR, filename)
                try:
                    with open(path, "r", encoding="utf-8") as handle:
                        data = json.load(handle)
                        if isinstance(data, list):
                            print(f"Loading {len(data)} records from {filename}")
                            records.extend(data)
                except Exception as e:
                    print(f"Error loading {filename}: {e}")
    
    if records:
        return records

    print("Warning: No valid data found in data/, using fallback.")
    return [
        {"text": "Kartımdan bilgim dışında para çekildi", "category": "FRAUD_UNAUTHORIZED_TX", "urgency": "RED"},
        {"text": "EFT yaptım gitmedi", "category": "TRANSFER_DELAY", "urgency": "YELLOW"},
        {"text": "Limit arttırımı istiyorum", "category": "CARD_LIMIT_CREDIT", "urgency": "GREEN"}
    ]

def hash_dataset(frame: pd.DataFrame) -> str:
    payload = "|".join(
        f"{row.text}::{row.category}::{row.urgency}" for row in frame.itertuples(index=False)
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def train():
    os.makedirs(MODELS_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)
    
    records = load_data()
    df = pd.DataFrame(records, columns=["text", "category", "urgency"])
    
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dataset_hash = hash_dataset(df)
    
    print(f"Loaded {len(df)} records. Dataset Hash: {dataset_hash[:8]}")

    # Stratified Split
    train_df, test_df = train_test_split(
        df, test_size=0.3, random_state=42, stratify=df["category"]
    )
    
    # Define Pipelines with Calibration
    # We calibrate the classifier for better probability estimates
    
    # Category Model
    cat_pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(max_features=1000, ngram_range=(1,2))),
        ('clf', CalibratedClassifierCV(
            estimator=LogisticRegression(class_weight='balanced', random_state=42),
            method='sigmoid',
            cv=3
        ))
    ])
    
    # Urgency Model
    urg_pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(max_features=1000, ngram_range=(1,2))),
        ('clf', CalibratedClassifierCV(
            estimator=LogisticRegression(class_weight='balanced', random_state=42),
            method='sigmoid', 
            cv=3
        ))
    ])
    
    print("Training Category Model...")
    cat_pipeline.fit(train_df["text"], train_df["category"])
    
    print("Training Urgency Model...")
    urg_pipeline.fit(train_df["text"], train_df["urgency"])
    
    # Evaluation
    print("Evaluating...")
    cat_preds = cat_pipeline.predict(test_df["text"])
    urg_preds = urg_pipeline.predict(test_df["text"])
    
    cat_report = classification_report(test_df["category"], cat_preds, output_dict=True)
    urg_report = classification_report(test_df["urgency"], urg_preds, output_dict=True)
    
    # Save Reports (Model Card Data)
    model_card = {
        "model_id": f"triage_v1_{timestamp}",
        "timestamp": timestamp,
        "dataset_hash": dataset_hash,
        "dataset_size": len(df),
        "train_size": len(train_df),
        "test_size": len(test_df),
        "metrics": {
            "category": cat_report,
            "urgency": urg_report
        },
        "parameters": {
            "vectorizer": "TfidfVectorizer(max_features=1000)",
            "classifier": "LogisticRegression(balanced) + CalibratedClassifierCV(sigmoid)"
        }
    }
    
    report_path = os.path.join(REPORTS_DIR, f"model_card_{timestamp}.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(model_card, f, indent=2, ensure_ascii=False)
        
    print(f"Model card saved: {report_path}")

    # Save Models
    cat_model_path = os.path.join(MODELS_DIR, f"category_model_{timestamp}.pkl")
    urg_model_path = os.path.join(MODELS_DIR, f"urgency_model_{timestamp}.pkl")
    
    joblib.dump(cat_pipeline, cat_model_path)
    joblib.dump(urg_pipeline, urg_model_path)
    
    # Update Latest Link
    latest_meta = {
        "timestamp": timestamp,
        "dataset_hash": dataset_hash,
        "category_model_path": cat_model_path,
        "urgency_model_path": urg_model_path,
        "model_card_path": report_path
    }
    
    with open(os.path.join(MODELS_DIR, "latest.json"), "w", encoding="utf-8") as f:
        json.dump(latest_meta, f, indent=2)
        
    print("Training Complete. Models updated.")

if __name__ == "__main__":
    train()
