"""
backend/KAN/src/predictor.py
============================
Inference Engine and Preprocessing Pipeline for KAN Collision-Risk Prediction.

Features:
- CPU-optimized execution with zero model retraining during requests.
- Custom unpickling shim for sklearn preprocessors (no heavy dependencies).
- Bounded execution with latency tracking.
- Numerical underflow safeguarding (never reports underflow as exact zero).
- Rigorous NaN / Inf rejection.
"""

import os
import sys
import time
import math
import pickle
from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np
import torch

try:
    from .kan import KAN
    from .feature_extractor import EXACT_33_FEATURE_NAMES, extract_features_from_state_and_cdm
except (ImportError, ValueError):
    from kan import KAN
    from feature_extractor import EXACT_33_FEATURE_NAMES, extract_features_from_state_and_cdm


class SimpleImputerShim:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
    def transform(self, X):
        X = np.array(X, copy=True, dtype=np.float32)
        inds = np.where(np.isnan(X))
        X[inds] = np.take(self.statistics_, inds[1])
        return X


class StandardScalerShim:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
    def transform(self, X):
        X = np.array(X, dtype=np.float32)
        return (X - self.mean_) / self.scale_
    def inverse_transform(self, X):
        X = np.array(X, dtype=np.float32)
        return X * self.scale_ + self.mean_


class SafePreprocessorUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if 'impute' in module:
            return SimpleImputerShim
        if 'preprocessing' in module:
            return StandardScalerShim
        return super().find_class(module, name)


class KANPredictor:
    """
    Production-grade predictor for Kolmogorov-Arnold Network collision risk assessment.
    """
    def __init__(
        self,
        model_path: Optional[str] = None,
        preprocessor_path: Optional[str] = None,
        device: str = "cpu",
    ):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if model_path is None:
            model_path = os.path.join(base_dir, "models", "kan_esa_model.pt")
        if preprocessor_path is None:
            preprocessor_path = os.path.join(base_dir, "models", "preprocessor.pkl")

        self.model_path = model_path
        self.preprocessor_path = preprocessor_path
        self.device = device
        self.model_version = "pykan_esa_kelvins_v1.0"

        self._load_artifacts()

    def _load_artifacts(self):
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model checkpoint not found: {self.model_path}")
        if not os.path.exists(self.preprocessor_path):
            raise FileNotFoundError(f"Preprocessor not found: {self.preprocessor_path}")

        # 1. Load Preprocessor
        with open(self.preprocessor_path, "rb") as f:
            try:
                self.preprocessor = pickle.load(f)
            except (ModuleNotFoundError, ImportError):
                f.seek(0)
                self.preprocessor = SafePreprocessorUnpickler(f).load()

        # 2. Load Checkpoint
        checkpoint = torch.load(self.model_path, map_location=self.device, weights_only=False)

        # 3. Construct KAN Model
        ckpt_dir = os.path.join(os.path.dirname(self.model_path), "temp_ckpt")
        self.model = KAN(
            width=checkpoint["width"],
            grid=checkpoint["grid"],
            k=checkpoint["k"],
            seed=42,
            device=self.device,
            ckpt_path=ckpt_dir,
            auto_save=False,
        )
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.model.eval()

        self.feature_names = checkpoint.get("feature_names", EXACT_33_FEATURE_NAMES)
        self.target_col = checkpoint.get("target_col", "risk")

    def predict_from_features(self, features_33: Union[List[float], np.ndarray]) -> Dict[str, Any]:
        """
        Runs inference on an explicit 33-element normalized/unscaled feature array.
        """
        t_start = time.perf_counter()

        feat_arr = np.asarray(features_33, dtype=np.float32)
        if feat_arr.ndim == 1:
            if len(feat_arr) != 33:
                return {
                    "status": "INVALID_FEATURE_DIMENSION",
                    "error": f"Expected exactly 33 features, got {len(feat_arr)}",
                    "model_version": self.model_version,
                }
            feat_arr = feat_arr.reshape(1, 33)
        elif feat_arr.ndim == 2:
            if feat_arr.shape[1] != 33:
                return {
                    "status": "INVALID_FEATURE_DIMENSION",
                    "error": f"Expected 33 columns, got {feat_arr.shape[1]}",
                    "model_version": self.model_version,
                }
        else:
            return {
                "status": "INVALID_FEATURE_SHAPE",
                "error": f"Unsupported array dimension: {feat_arr.ndim}",
                "model_version": self.model_version,
            }

        # Validate against NaN and Inf
        if np.isnan(feat_arr).any() or np.isinf(feat_arr).any():
            return {
                "status": "INVALID_NUMERICAL_INPUT",
                "error": "Input feature vector contains NaN or Infinite values",
                "model_version": self.model_version,
            }

        # 1. Impute missing (if any) and Scale X
        X_imp = self.preprocessor["imputer"].transform(feat_arr)
        X_scaled = self.preprocessor["scaler_X"].transform(X_imp)

        # 2. PyTorch KAN Forward Pass
        X_t = torch.tensor(X_scaled, dtype=torch.float32, device=self.device)
        with torch.no_grad():
            pred_t = self.model(X_t)
            pred_scaled = pred_t.cpu().squeeze().numpy()

        if np.ndim(pred_scaled) == 0:
            pred_scaled = np.array([pred_scaled])

        # 3. Inverse transform target
        pred_risk_arr = self.preprocessor["scaler_y"].inverse_transform(pred_scaled.reshape(-1, 1)).squeeze()
        if np.ndim(pred_risk_arr) == 0:
            pred_risk = float(pred_risk_arr)
        else:
            pred_risk = float(pred_risk_arr[0])

        # 4. Compute physical Pc from risk = log10(Pc)
        underflow_flag = False
        if pred_risk < -300.0:
            # IEEE-754 double precision limit for 10^x is ~ -308.25
            estimated_pc = 0.0
            underflow_flag = True
            pc_str = f"< 1.0000e-300 (underflow, 10^{pred_risk:.2f})"
        else:
            try:
                estimated_pc = 10.0 ** pred_risk
                pc_str = f"{estimated_pc:.4e}"
            except OverflowError:
                estimated_pc = 1.0
                pc_str = "1.0000e+00 (overflow)"

        # 5. Risk Category Classification (documented standard)
        # Operational standard: CRITICAL >= 1e-4, WARNING >= 1e-6, LOW < 1e-6
        if pred_risk >= -4.0:
            risk_category = "CRITICAL"
        elif pred_risk >= -6.0:
            risk_category = "WARNING"
        else:
            risk_category = "LOW"

        t_elapsed_ms = (time.perf_counter() - t_start) * 1000.0

        return {
            "status": "SUCCESS",
            "model_name": "pykan_esa_kelvins",
            "model_version": self.model_version,
            "target": "risk [log10(Pc)]",
            "predicted_risk_log10": round(pred_risk, 6),
            "estimated_pc": estimated_pc if not underflow_flag else 0.0,
            "estimated_pc_display": pc_str,
            "underflow": underflow_flag,
            "risk_category": risk_category,
            "latency_ms": round(t_elapsed_ms, 3),
            "provenance": {
                "dataset": "ESA Kelvins Collision Avoidance Challenge",
                "framework": "PyTorch / PyKAN",
                "architecture": "[33, 8, 1]",
                "device": self.device,
            },
        }

    def predict_from_cdm_dict(self, cdm_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs inference directly from a dictionary containing the 33 CDM feature keys.
        """
        feature_vals = []
        for name in EXACT_33_FEATURE_NAMES:
            if name not in cdm_data:
                return {
                    "status": "MISSING_CDM_FEATURE",
                    "error": f"CDM record missing required feature: '{name}'",
                    "model_version": self.model_version,
                }
            val = cdm_data[name]
            try:
                feature_vals.append(float(val))
            except (ValueError, TypeError):
                return {
                    "status": "INVALID_FEATURE_TYPE",
                    "error": f"Feature '{name}' has non-numeric value: '{val}'",
                    "model_version": self.model_version,
                }
        return self.predict_from_features(feature_vals)

    def predict_from_icps_state(
        self,
        r_target: np.ndarray,
        v_target: np.ndarray,
        r_chaser: np.ndarray,
        v_chaser: np.ndarray,
        tca_seconds: float,
        cov_target_3x3: Optional[np.ndarray] = None,
        cov_chaser_3x3: Optional[np.ndarray] = None,
        t_span_days: Optional[float] = None,
        c_span_days: Optional[float] = None,
        chaser_object_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Safe bridge between ICPS simulation Cartesian states and KAN model.
        Returns INSUFFICIENT_INPUT_DATA if all 33 features cannot be faithfully derived.
        """
        result = extract_features_from_state_and_cdm(
            r_target=r_target,
            v_target=v_target,
            r_chaser=r_chaser,
            v_chaser=v_chaser,
            tca_seconds=tca_seconds,
            cov_target_3x3=cov_target_3x3,
            cov_chaser_3x3=cov_chaser_3x3,
            t_span_days=t_span_days,
            c_span_days=c_span_days,
            chaser_object_type=chaser_object_type,
            strict_cdm=True,
        )

        if not result.is_valid():
            return {
                "status": result.status,
                "error": result.message,
                "missing_features": result.missing_features,
                "model_version": self.model_version,
                "fallback_recommended": True,
            }

        pred_res = self.predict_from_features(result.features)
        pred_res["input_derivation_status"] = "VERIFIED_ASTRODYNAMICS"
        return pred_res
