# ICPS — Kolmogorov-Arnold Network (KAN) Backend

## 1. Overview
This module provides empirical collision-risk assessment for the ICPS (Satellite Collision Avoidance System) using Kolmogorov-Arnold Networks (KAN). The model is trained on the European Space Agency (ESA) Kelvins Collision Avoidance Challenge dataset.

## 2. Directory Structure
```
backend/KAN/
├── api/
│   ├── app.py                  # FastAPI REST microservice
│   └── schemas.py              # Pydantic v2 input/output schemas
├── models/
│   ├── kan_esa_model.pt        # Trained PyKAN model checkpoint (5.45 MB)
│   ├── kan_collision_model.pt  # Secondary prototype checkpoint (502 KB)
│   ├── preprocessor.pkl        # Serialized StandardScaler & SimpleImputer
│   ├── model_metadata.json     # Architecture specification & test metrics
│   ├── feature_names.json      # Exact 33 feature names
│   ├── evaluation_metrics.csv  # MAE, RMSE, R² comparison against Ridge
│   └── extraction_manifest.json# Source commit & SHA256 hashes
├── notebooks/
│   └── kan_collision_prediction.ipynb # Training notebook
├── src/
│   ├── feature_extractor.py    # ICPS ECI to 33 ESA Kelvins feature adapter
│   ├── predictor.py            # KANPredictor inference engine
│   └── kan/                    # Pure-Python PyKAN layer implementation
├── tests/
│   └── test_kan_model.py       # Unit tests for loading, transforms & inference
├── requirements.txt            # Python dependencies
└── README.md                   # This documentation
```

## 3. Mathematical & Model Specifications
- **Model Type:** PyKAN (`from kan import KAN`)
- **Architecture:** `[33, 8, 1]` (33 input features $\to$ 8 hidden spline nodes $\to$ 1 scalar output)
- **Spline Basis:** Uniform cubic B-splines ($k = 3$) with grid size $G = 5$
- **Target Variable:** $\text{risk} = \log_{10}(P_c)$
- **Physical Collision Probability:** $P_c = 10^{\text{risk}}$
- **Regularization:** Sparsity $L_1$ penalty on spline coefficients ($\lambda = 0.005$)
- **Optimization:** Quasi-Newton LBFGS optimizer ($lr = 0.01$, 35 steps)

## 4. API Endpoints
- `GET /api/v1/health`: Service health check.
- `GET /api/v1/model-info`: Returns model architecture, feature names, and benchmark metrics.
- `POST /api/v1/predict/collision-risk`: Ingests physical state vectors or direct 33 features and returns predicted risk ($\log_{10} P_c$), estimated $P_c$, and risk classification.

## 5. Safety & Physics Fallback Policy
The KAN model is strictly an empirical risk assessment tool. It does **not** replace the authoritative D1/D2 physics engine (RK4 propagation, Foster $P_c$, manoeuvre planning). If required physical quantities or CDM parameters are missing, the service returns `status: INSUFFICIENT_INPUT_DATA` with `fallback_to_physics: True`.
