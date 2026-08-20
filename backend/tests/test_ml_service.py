import numpy as np
import pytest
from pydantic import ValidationError

from app.schemas.ml import MLInferenceRequest, MLInferenceResponse
from app.services import ml_service
from app.services.ml_service import (
    FEATURE_COLUMNS,
    GAP_CLASS_INDEX,
    predict_gap,
)

VALID_REQUEST = {
    "zip_code": "90001",
    "population": 25000,
    "zip_provider_share_of_state": 0.05,
    "individual_provider_ratio": 0.75,
    "organization_provider_ratio": 0.25,
}

REQUIRED_RESPONSE_FIELDS = {
    "access_gap_score",
    "gap_category",
    "recommendation",
    "confidence",
    "explanation",
    "model_version",
}


def _reset_model():
    ml_service._model = None
    ml_service._metadata = None


# ---------------------------------------------------------------------------
# Schema / input contract
# ---------------------------------------------------------------------------

def test_valid_request_parses():
    request = MLInferenceRequest(**VALID_REQUEST)
    assert request.zip_code == "90001"
    assert request.population == 25000


def test_request_requires_all_contract_fields():
    for missing in VALID_REQUEST:
        partial = {key: value for key, value in VALID_REQUEST.items() if key != missing}
        with pytest.raises(ValidationError):
            MLInferenceRequest(**partial)


def test_request_rejects_negative_population():
    bad = dict(VALID_REQUEST, population=-1)
    with pytest.raises(ValidationError):
        MLInferenceRequest(**bad)


def test_request_rejects_ratio_outside_unit_interval():
    for field in (
        "zip_provider_share_of_state",
        "individual_provider_ratio",
        "organization_provider_ratio",
    ):
        for value in (-0.1, 1.1):
            with pytest.raises(ValidationError):
                MLInferenceRequest(**dict(VALID_REQUEST, **{field: value}))


def test_contract_input_fields_are_exact():
    fields = set(MLInferenceRequest.model_fields)
    assert fields == {
        "zip_code",
        "population",
        "zip_provider_share_of_state",
        "individual_provider_ratio",
        "organization_provider_ratio",
    }


def test_model_features_are_exactly_the_four_numeric_columns():
    assert FEATURE_COLUMNS == [
        "population",
        "zip_provider_share_of_state",
        "individual_provider_ratio",
        "organization_provider_ratio",
    ]
    assert "zip_code" not in FEATURE_COLUMNS


# ---------------------------------------------------------------------------
# Service logic with a mocked model (no artifact dependency)
# ---------------------------------------------------------------------------

class FakePipeline:
    def __init__(self, proba, classes=(0, 1)):
        self._proba = proba
        self.classes_ = np.array(classes)
        self.n_features_in_ = len(FEATURE_COLUMNS)
        self.feature_names_in_ = np.array(FEATURE_COLUMNS)

    def predict_proba(self, features):
        return np.array([self._proba])


def _mock_model(proba, metadata=None):
    _reset_model()
    ml_service._model = FakePipeline(proba)
    ml_service._metadata = metadata or {
        "model_version": "v2.4-rf-only",
        "feature_importances": {
            "population": 0.44,
            "zip_provider_share_of_state": 0.39,
            "individual_provider_ratio": 0.09,
            "organization_provider_ratio": 0.08,
        },
    }


def test_feature_vector_excludes_zip_code():
    request = MLInferenceRequest(**VALID_REQUEST)
    vector = ml_service._build_feature_vector(request)
    assert vector.shape == (1, 4)
    assert vector[0].tolist() == [
        25000.0,
        0.05,
        0.75,
        0.25,
    ]
    assert "zip_code" not in ml_service._build_feature_vector.__name__  # sanity
    # The request includes 5 fields; only 4 become features.
    assert vector.shape[1] == len(FEATURE_COLUMNS)


def test_predict_gap_returns_full_contract():
    _mock_model([0.2, 0.8])
    response = predict_gap(MLInferenceRequest(**VALID_REQUEST))
    assert isinstance(response, MLInferenceResponse)
    assert REQUIRED_RESPONSE_FIELDS == set(response.model_dump())


def test_access_gap_score_is_probability_of_gap_class():
    _mock_model([0.1, 0.9])
    response = predict_gap(MLInferenceRequest(**VALID_REQUEST))
    assert response.access_gap_score == pytest.approx(0.9)


def test_gap_category_high_when_score_above_high_threshold():
    _mock_model([0.1, 0.9])
    response = predict_gap(MLInferenceRequest(**VALID_REQUEST))
    assert response.gap_category == "high"


def test_gap_category_medium_when_score_between_thresholds():
    _mock_model([0.5, 0.5])
    response = predict_gap(MLInferenceRequest(**VALID_REQUEST))
    assert response.gap_category == "medium"


def test_gap_category_low_when_score_below_medium_threshold():
    _mock_model([0.9, 0.1])
    response = predict_gap(MLInferenceRequest(**VALID_REQUEST))
    assert response.gap_category == "low"


def test_confidence_is_max_probability():
    _mock_model([0.3, 0.7])
    response = predict_gap(MLInferenceRequest(**VALID_REQUEST))
    assert response.confidence == pytest.approx(0.7)


def test_model_version_from_metadata():
    _mock_model([0.2, 0.8])
    response = predict_gap(MLInferenceRequest(**VALID_REQUEST))
    assert response.model_version == "v2.4-rf-only"


def test_recommendation_present_for_each_category():
    for proba in ([0.1, 0.9], [0.5, 0.5], [0.9, 0.1]):
        _mock_model(proba)
        response = predict_gap(MLInferenceRequest(**VALID_REQUEST))
        assert response.recommendation
        assert response.explanation


def test_explanation_lists_features_by_importance():
    _mock_model([0.2, 0.8])
    response = predict_gap(MLInferenceRequest(**VALID_REQUEST))
    assert response.explanation[0].startswith("Population")
    assert len(response.explanation) == 4


def test_zip_code_value_does_not_affect_prediction():
    _mock_model([0.2, 0.8])
    base = predict_gap(MLInferenceRequest(**VALID_REQUEST))
    different_zip = predict_gap(
        MLInferenceRequest(**{**VALID_REQUEST, "zip_code": "99999"})
    )
    assert base.access_gap_score == different_zip.access_gap_score
    assert base.gap_category == different_zip.gap_category


# ---------------------------------------------------------------------------
# Real artifact integration (model is available locally)
# ---------------------------------------------------------------------------

def test_real_model_artifact_exists():
    assert ml_service.FINAL_MODEL_PATH.exists()
    assert ml_service.MODEL_METADATA_PATH.exists()


def test_real_model_uses_only_four_features():
    _reset_model()
    model, metadata = ml_service.load_model()
    assert model.n_features_in_ == 4
    assert list(metadata["features_used"]) == FEATURE_COLUMNS


def test_real_model_predict_gap_matches_contract():
    _reset_model()
    response = predict_gap(MLInferenceRequest(**VALID_REQUEST))
    assert isinstance(response, MLInferenceResponse)
    assert 0.0 <= response.access_gap_score <= 1.0
    assert response.gap_category in {"high", "medium", "low"}
    assert response.model_version == "v2.4-rf-only"
    assert len(response.explanation) == 4
    assert response.recommendation