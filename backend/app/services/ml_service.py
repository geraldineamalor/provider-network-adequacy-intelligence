from pathlib import Path

import joblib
import numpy as np

from app.schemas.ml import MLInferenceRequest, MLInferenceResponse

# ML-2 model artifacts (real trained model, v3.2-specialty-context-merged)
MODEL_DIR = Path(__file__).resolve().parent.parent / "models"
FINAL_MODEL_PATH = MODEL_DIR / "final_model.joblib"
MODEL_METADATA_PATH = MODEL_DIR / "model_metadata.joblib"

# The trained Random Forest uses these five numeric features, in this
# exact order. zip_code and primary_taxonomy are metadata and must
# never be added as features.
FEATURE_COLUMNS = [
    "population",
    "zip_provider_share_of_state",
    "individual_provider_ratio",
    "organization_provider_ratio",
    "specialty_diversity",
]

# Category thresholds applied to the access gap score (0.0 to 1.0).
HIGH_GAP_THRESHOLD = 0.66
MEDIUM_GAP_THRESHOLD = 0.33

# Gap probability class index (model.classes_ == [0, 1]).
GAP_CLASS_INDEX = 1

_model = None
_metadata = None


def load_model() -> tuple[object, dict]:
    """Load the ML-2 model and its metadata once and cache them."""
    global _model, _metadata
    if _model is None:
        _model = joblib.load(FINAL_MODEL_PATH)
        _metadata = joblib.load(MODEL_METADATA_PATH)
    return _model, _metadata


def _build_feature_vector(request: MLInferenceRequest) -> np.ndarray:
    """Build the 5-feature vector for the model. zip_code is excluded."""
    return np.array(
        [
            [
                float(request.population),
                float(request.zip_provider_share_of_state),
                float(request.individual_provider_ratio),
                float(request.organization_provider_ratio),
                float(request.specialty_diversity),
            ]
        ],
        dtype=float,
    )


def _gap_category(score: float) -> str:
    if score >= HIGH_GAP_THRESHOLD:
        return "high"
    if score >= MEDIUM_GAP_THRESHOLD:
        return "medium"
    return "low"


def _feature_descriptions(request: MLInferenceRequest) -> dict[str, str]:
    """Human-readable description for each feature, used in explanation."""
    return {
        "population": f"Population {request.population}",
        "zip_provider_share_of_state": (
            f"Share of state providers {request.zip_provider_share_of_state:.3f}"
        ),
        "individual_provider_ratio": (
            f"Individual provider ratio {request.individual_provider_ratio:.3f}"
        ),
        "organization_provider_ratio": (
            f"Organization provider ratio {request.organization_provider_ratio:.3f}"
        ),
        "specialty_diversity": (
            f"Specialty diversity {request.specialty_diversity:.3f}"
        ),
    }


def _build_explanation(
    request: MLInferenceRequest, feature_importances: dict[str, float]
) -> list[str]:
    """Explain the prediction using the most important contributing features."""
    ranked = sorted(
        feature_importances.items(), key=lambda item: item[1], reverse=True
    )
    descriptions = _feature_descriptions(request)
    return [descriptions[name] for name, _ in ranked]


def _build_recommendation(
    category: str, score: float, top_feature: str
) -> str:
    if category == "high":
        return (
            f"Prioritize recruitment: high gap score ({score:.2f}) driven by "
            f"{top_feature}."
        )
    if category == "medium":
        return (
            f"Monitor: medium gap score ({score:.2f}) driven by {top_feature}."
        )
    return (
        f"No immediate action: low gap score ({score:.2f})."
    )


def predict_gap(request: MLInferenceRequest) -> MLInferenceResponse:
    """Run ML-2 inference for a single ZIP area.

    The model is a binary Random Forest; the access gap score is the
    predicted probability of the gap class (class 1).
    The prediction field contains the predicted class (0 or 1).
    """
    model, metadata = load_model()

    features = _build_feature_vector(request)
    proba = model.predict_proba(features)[0]

    access_gap_score = float(proba[GAP_CLASS_INDEX])
    confidence = float(max(proba))
    category = _gap_category(access_gap_score)
    prediction = model.predict(features)

    # Handle both array and scalar return from model.predict()
    if isinstance(prediction, np.ndarray):
        prediction = int(prediction[0])
    else:
        prediction = int(prediction)

    importances = metadata.get("feature_importances", {})
    explanation = _build_explanation(request, importances)
    top_feature = explanation[0] if explanation else "contextual features"
    recommendation = _build_recommendation(category, access_gap_score, top_feature)

    return MLInferenceResponse(
        access_gap_score=access_gap_score,
        gap_category=category,
        prediction=prediction,
        confidence=confidence,
        explanation=explanation,
        model_version=metadata.get("model_version", "unknown"),
        recommendation=recommendation,
    )