import joblib
import logging
import json
from pathlib import Path


class TriageEngine:
    # Map model output labels to API contract labels
    URGENCY_MAPPING = {
        "RED": "HIGH",
        "YELLOW": "MEDIUM",
        "GREEN": "LOW",
        # Passthrough for already-correct labels
        "HIGH": "HIGH",
        "MEDIUM": "MEDIUM",
        "LOW": "LOW",
    }

    def __init__(self):
        self.category_model = None
        self.urgency_model = None
        self.model_loaded = False
        self.logger = logging.getLogger("complaintops.triage_model")
        self._load_models()

    def _load_models(self):
        try:
            # Use pathlib for cross-platform compatibility
            base_dir = Path(__file__).parent.parent.parent
            metadata_path = base_dir / "models" / "latest.json"

            if metadata_path.exists():
                with open(metadata_path, "r", encoding="utf-8") as handle:
                    metadata = json.load(handle)

                # Resolve relative paths from base_dir
                category_path = base_dir / metadata.get("category_model_path", "")
                urgency_path = base_dir / metadata.get("urgency_model_path", "")

                if category_path.exists() and urgency_path.exists():
                    self.category_model = joblib.load(str(category_path))
                    self.urgency_model = joblib.load(str(urgency_path))
                    self.logger.info("✅ Models loaded from %s", category_path.parent)
                else:
                    self.logger.warning("Model files not found at %s", category_path)
            else:
                # Fallback to legacy paths
                legacy_cat = base_dir / "models" / "category_model.pkl"
                legacy_urg = base_dir / "models" / "urgency_model.pkl"
                if legacy_cat.exists() and legacy_urg.exists():
                    self.category_model = joblib.load(str(legacy_cat))
                    self.urgency_model = joblib.load(str(legacy_urg))
                    self.logger.info("✅ Models loaded from legacy paths")
                else:
                    self.logger.warning("Models not found. Please run train_triage_model.py first.")
        except Exception as e:
            self.logger.error("❌ Error loading models: %s", e)

        self.model_loaded = bool(self.category_model and self.urgency_model)

    def predict(self, text: str):
        if not self.model_loaded:
            return {
                "category": "UNKNOWN",
                "category_confidence": 0.0,
                "urgency": "LOW",
                "urgency_confidence": 0.0,
                "model_loaded": False,
            }

        # Predict Category
        cat_pred = self.category_model.predict([text])[0]
        cat_probs = self.category_model.predict_proba([text])[0]
        cat_conf = max(cat_probs)

        # Predict Urgency
        raw_urgency = self.urgency_model.predict([text])[0]
        urg_probs = self.urgency_model.predict_proba([text])[0]
        urg_conf = max(urg_probs)

        # Map to API contract labels (RED/YELLOW/GREEN -> HIGH/MEDIUM/LOW)
        mapped_urgency = self.URGENCY_MAPPING.get(str(raw_urgency).upper(), "LOW")

        return {
            "category": cat_pred,
            "category_confidence": float(cat_conf),
            "urgency": mapped_urgency,
            "urgency_confidence": float(urg_conf),
            "model_loaded": True,
        }


triage_engine = TriageEngine()

