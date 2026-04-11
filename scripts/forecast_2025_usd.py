#!/usr/bin/env python3
"""
Infer price-scale transformation and generate 2025 forecasts in USD/oz.

Outputs:
- results/forecasts/predictions_2025_best_model.csv
- results/forecasts/predictions_2025_all_models.csv
- results/forecasts/historical_vs_2025_forecast_usd.png
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.isotonic import IsotonicRegression

import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"
MODEL_DIR = BACKEND_DIR / "models" / "saved_models"
OUT_DIR = REPO_ROOT / "results" / "forecasts"

sys.path.insert(0, str(BACKEND_DIR))

from data_loader import GoldDataLoader  # noqa: E402
from feature_engineering import FeatureEngineer  # noqa: E402
from model_trainer import ModelTrainer  # noqa: E402


# Approximate annual average spot gold prices in USD per troy ounce.
# These anchors are used to infer a non-linear monotonic transformation
# rather than assuming a fixed multiplier.
REFERENCE_GOLD_USD_BY_YEAR = {
    2010: 1224.0,
    2011: 1571.0,
    2012: 1668.0,
    2013: 1411.0,
    2014: 1266.0,
    2015: 1160.0,
    2016: 1251.0,
    2017: 1257.0,
    2018: 1268.0,
    2019: 1393.0,
    2020: 1769.0,
    2021: 1799.0,
    2022: 1800.0,
    2023: 1943.0,
    2024: 2386.0,
}


@dataclass
class ScaleAnalysis:
    classification: str
    reason: str
    min_val: float
    max_val: float
    mean_val: float
    std_val: float


def analyze_price_scale(close_series: pd.Series) -> ScaleAnalysis:
    """Classify whether the series looks normalized, scaled, or derived."""
    min_val = float(close_series.min())
    max_val = float(close_series.max())
    mean_val = float(close_series.mean())
    std_val = float(close_series.std())

    if min_val >= -0.1 and max_val <= 1.1:
        return ScaleAnalysis(
            classification="normalized",
            reason="Values lie approximately in [0, 1], indicating normalization.",
            min_val=min_val,
            max_val=max_val,
            mean_val=mean_val,
            std_val=std_val,
        )

    # Typical gold spot USD/oz in 2010-2024 is mostly around ~1050-2500.
    # A series concentrated around ~100-300 likely represents a derived
    # instrument scale (ETF-like / transformed series).
    if max_val < 500:
        return ScaleAnalysis(
            classification="derived_instrument_or_scaled",
            reason=(
                "Range is far below typical spot-gold USD/oz levels and likely "
                "represents a derived instrument scale (e.g., ETF-like share price) "
                "or transformed gold series."
            ),
            min_val=min_val,
            max_val=max_val,
            mean_val=mean_val,
            std_val=std_val,
        )

    return ScaleAnalysis(
        classification="scaled_but_near_market_range",
        reason="Range overlaps plausible USD/oz levels but may still require calibration.",
        min_val=min_val,
        max_val=max_val,
        mean_val=mean_val,
        std_val=std_val,
    )


def infer_usd_transform(df: pd.DataFrame, close_col: str, date_col: str = "date") -> Tuple[IsotonicRegression, pd.DataFrame]:
    """
    Infer monotonic non-linear mapping from dataset scale -> USD/oz.

    Uses annual trend matching between dataset annual means and reference annual
    spot-gold anchors, then fits isotonic regression for a non-fixed transform.
    """
    work = df[[date_col, close_col]].copy()
    work[date_col] = pd.to_datetime(work[date_col])
    work["year"] = work[date_col].dt.year

    annual_orig = work.groupby("year", as_index=False)[close_col].mean()
    annual_orig.rename(columns={close_col: "orig_annual_mean"}, inplace=True)

    ref = pd.DataFrame(
        {
            "year": list(REFERENCE_GOLD_USD_BY_YEAR.keys()),
            "ref_usd_annual_mean": list(REFERENCE_GOLD_USD_BY_YEAR.values()),
        }
    )

    merged = annual_orig.merge(ref, on="year", how="inner").sort_values("year")
    if len(merged) < 5:
        raise ValueError("Not enough overlap years to infer USD transformation.")

    iso = IsotonicRegression(increasing=True, out_of_bounds="clip")
    iso.fit(merged["orig_annual_mean"].values, merged["ref_usd_annual_mean"].values)

    merged["mapped_usd_annual_mean"] = iso.predict(merged["orig_annual_mean"].values)
    merged["abs_error"] = (merged["mapped_usd_annual_mean"] - merged["ref_usd_annual_mean"]).abs()
    merged["pct_error"] = 100.0 * merged["abs_error"] / merged["ref_usd_annual_mean"]

    return iso, merged


def transform_to_usd(values: np.ndarray, iso: IsotonicRegression, annual_fit: pd.DataFrame) -> np.ndarray:
    """
    Transform original-scale values to USD with monotonic mapping and
    linear tail extrapolation outside fitted annual range.
    """
    x = np.asarray(values, dtype=float)
    x_fit = annual_fit["orig_annual_mean"].to_numpy(dtype=float)
    y_fit = annual_fit["ref_usd_annual_mean"].to_numpy(dtype=float)

    x_min, x_max = float(x_fit.min()), float(x_fit.max())
    y_min, y_max = float(y_fit[np.argmin(x_fit)]), float(y_fit[np.argmax(x_fit)])

    k = min(4, len(x_fit))
    low_idx = np.argsort(x_fit)[:k]
    high_idx = np.argsort(x_fit)[-k:]

    low_slope = np.polyfit(x_fit[low_idx], y_fit[low_idx], 1)[0] if k >= 2 else 8.0
    high_slope = np.polyfit(x_fit[high_idx], y_fit[high_idx], 1)[0] if k >= 2 else 8.0

    clipped = np.clip(x, x_min, x_max)
    y = iso.predict(clipped)

    low_mask = x < x_min
    high_mask = x > x_max

    if np.any(low_mask):
        y[low_mask] = y_min + low_slope * (x[low_mask] - x_min)
    if np.any(high_mask):
        y[high_mask] = y_max + high_slope * (x[high_mask] - x_max)

    return y


def _compute_rsi(history: List[float], period: int = 14) -> float:
    if len(history) <= period:
        return 50.0

    prices = pd.Series(history[-(period + 1):], dtype=float)
    delta = prices.diff().dropna()
    gains = delta.where(delta > 0, 0.0)
    losses = -delta.where(delta < 0, 0.0)

    avg_gain = gains.mean()
    avg_loss = losses.mean()
    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    return float(100 - (100 / (1 + rs)))


def _update_time_features(features: Dict[str, float], dt: pd.Timestamp) -> None:
    month = dt.month
    quarter = dt.quarter
    dow = dt.dayofweek
    doy = dt.dayofyear

    if "Month" in features:
        features["Month"] = float(month)
    if "Quarter" in features:
        features["Quarter"] = float(quarter)
    if "DayOfWeek" in features:
        features["DayOfWeek"] = float(dow)
    if "DayOfYear" in features:
        features["DayOfYear"] = float(doy)
    if "IsYearEnd" in features:
        features["IsYearEnd"] = float(dt.is_year_end)
    if "IsQuarterEnd" in features:
        features["IsQuarterEnd"] = float(dt.is_quarter_end)

    if "Month_sin" in features:
        features["Month_sin"] = float(np.sin(2 * np.pi * month / 12))
    if "Month_cos" in features:
        features["Month_cos"] = float(np.cos(2 * np.pi * month / 12))
    if "DayOfWeek_sin" in features:
        features["DayOfWeek_sin"] = float(np.sin(2 * np.pi * dow / 7))
    if "DayOfWeek_cos" in features:
        features["DayOfWeek_cos"] = float(np.cos(2 * np.pi * dow / 7))
    if "DayOfYear_sin" in features:
        features["DayOfYear_sin"] = float(np.sin(2 * np.pi * doy / 365))
    if "DayOfYear_cos" in features:
        features["DayOfYear_cos"] = float(np.cos(2 * np.pi * doy / 365))


def _build_next_features(base_features: Dict[str, float], history: List[float], feature_names: List[str], next_date: pd.Timestamp) -> Dict[str, float]:
    features = base_features.copy()
    last_price = float(history[-1])

    _update_time_features(features, next_date)

    for lag in [1, 2, 3, 5, 7]:
        col = f"Lag_gold_close_{lag}"
        if col in feature_names:
            features[col] = float(history[-lag]) if len(history) >= lag else last_price

    for window in [7, 14, 30]:
        window_prices = history[-min(window, len(history)):]
        m = float(np.mean(window_prices))
        s = float(np.std(window_prices))
        mi = float(np.min(window_prices))
        ma = float(np.max(window_prices))

        if f"Rolling_Mean_gold_{window}" in feature_names:
            features[f"Rolling_Mean_gold_{window}"] = m
        if f"Rolling_Std_gold_{window}" in feature_names:
            features[f"Rolling_Std_gold_{window}"] = s
        if f"Rolling_Min_gold_{window}" in feature_names:
            features[f"Rolling_Min_gold_{window}"] = mi
        if f"Rolling_Max_gold_{window}" in feature_names:
            features[f"Rolling_Max_gold_{window}"] = ma

    for period in [10, 20, 50]:
        col = f"SMA_gold_{period}"
        if col in feature_names:
            features[col] = float(np.mean(history[-min(period, len(history)):]))

    for period in [10, 20]:
        col = f"EMA_gold_{period}"
        if col in feature_names:
            prev = float(features.get(col, last_price))
            alpha = 2.0 / (period + 1)
            features[col] = float(alpha * last_price + (1 - alpha) * prev)

    if "RSI_gold_14" in feature_names:
        features["RSI_gold_14"] = _compute_rsi(history, period=14)

    if "Returns_gold" in feature_names:
        prev_price = float(history[-2]) if len(history) >= 2 else last_price
        features["Returns_gold"] = float((last_price - prev_price) / prev_price) if prev_price != 0 else 0.0

    if "Volatility_gold_20" in feature_names:
        returns = pd.Series(history, dtype=float).pct_change().dropna().tail(20)
        features["Volatility_gold_20"] = float(returns.std()) if len(returns) else 0.0

    if any(c in feature_names for c in ["MACD_gold", "MACD_Signal_gold", "MACD_Hist_gold"]):
        prev_ema12 = float(features.get("EMA_gold_12", last_price))
        prev_ema26 = float(features.get("EMA_gold_26", last_price))
        ema12 = (2.0 / 13.0) * last_price + (11.0 / 13.0) * prev_ema12
        ema26 = (2.0 / 27.0) * last_price + (25.0 / 27.0) * prev_ema26
        macd = float(ema12 - ema26)
        prev_sig = float(features.get("MACD_Signal_gold", macd))
        sig = (2.0 / 10.0) * macd + (8.0 / 10.0) * prev_sig

        if "EMA_gold_12" in feature_names:
            features["EMA_gold_12"] = float(ema12)
        if "EMA_gold_26" in feature_names:
            features["EMA_gold_26"] = float(ema26)
        if "MACD_gold" in feature_names:
            features["MACD_gold"] = macd
        if "MACD_Signal_gold" in feature_names:
            features["MACD_Signal_gold"] = float(sig)
        if "MACD_Hist_gold" in feature_names:
            features["MACD_Hist_gold"] = float(macd - sig)

    if any(c in feature_names for c in ["BB_Upper_gold", "BB_Lower_gold", "BB_Middle_gold", "BB_Width_gold"]):
        bb = history[-min(20, len(history)):]
        bb_m = float(np.mean(bb))
        bb_s = float(np.std(bb))
        if "BB_Middle_gold" in feature_names:
            features["BB_Middle_gold"] = bb_m
        if "BB_Upper_gold" in feature_names:
            features["BB_Upper_gold"] = bb_m + 2 * bb_s
        if "BB_Lower_gold" in feature_names:
            features["BB_Lower_gold"] = bb_m - 2 * bb_s
        if "BB_Width_gold" in feature_names:
            features["BB_Width_gold"] = 4 * bb_s

    # Update same-day gold components if present.
    for c in ["gold_open", "gold_high", "gold_low"]:
        if c in feature_names:
            features[c] = last_price

    if "Ratio_Gold_Silver" in feature_names and "silver_close" in features:
        features["Ratio_Gold_Silver"] = last_price / (float(features["silver_close"]) + 1e-9)
    if "Ratio_Gold_Platinum" in feature_names and "platinum_close" in features:
        features["Ratio_Gold_Platinum"] = last_price / (float(features["platinum_close"]) + 1e-9)
    if "Ratio_Gold_Oil" in feature_names and "oil_close" in features:
        features["Ratio_Gold_Oil"] = last_price / (float(features["oil_close"]) + 1e-9)

    # Numerical guardrails for recursive feature generation.
    for k, v in list(features.items()):
        if not np.isfinite(v):
            features[k] = 0.0
        else:
            features[k] = float(np.clip(v, -1e6, 1e6))

    return features


def generate_2025_predictions(data: Dict[str, np.ndarray], trainer: ModelTrainer, model_id: str) -> pd.DataFrame:
    feature_names = list(data["feature_names"])
    df_full = data["df_full"].copy()

    date_col = "Date" if "Date" in df_full.columns else "date"
    target_col = "gold_close" if "gold_close" in df_full.columns else "Close_gold"

    base_row = df_full.iloc[-1]
    base_features = {}
    for f in feature_names:
        v = base_row[f] if f in base_row else 0.0
        base_features[f] = float(v) if isinstance(v, (int, float, np.integer, np.floating)) else 0.0

    history = df_full[target_col].astype(float).tolist()
    base_history = history.copy()
    start_date = pd.Timestamp(df_full[date_col].iloc[-1]) + pd.Timedelta(days=1)
    start_date = max(start_date, pd.Timestamp("2025-01-01"))
    future_dates = pd.date_range(start=start_date, periods=365, freq="D")

    model = trainer.models[model_id]

    if model_id == "linear_regression" and model_id in trainer.scalers:
        expected_n = int(trainer.scalers[model_id].n_features_in_)
    else:
        expected_n = int(getattr(model, "n_features_in_", len(feature_names)))

    if len(feature_names) > expected_n:
        feature_names = feature_names[:expected_n]
    elif len(feature_names) < expected_n:
        # Keep compatibility with artifacts expecting a larger feature vector.
        pad_count = expected_n - len(feature_names)
        for i in range(pad_count):
            pad_name = f"__pad_{i}"
            feature_names.append(pad_name)
            base_features[pad_name] = 0.0
    preds = []
    rolling_features = base_features.copy()
    fixed_lower = min(base_history) * 0.8
    fixed_upper = max(base_history) * 1.2

    for dt in future_dates:
        rolling_features = _build_next_features(rolling_features, history, feature_names, dt)
        x = np.array([[rolling_features[f] for f in feature_names]], dtype=float)
        x = np.nan_to_num(x, nan=0.0, posinf=1e6, neginf=-1e6)
        x = np.clip(x, -1e6, 1e6)
        if model_id == "linear_regression" and model_id in trainer.scalers:
            x = trainer.scalers[model_id].transform(x)

        yhat = float(model.predict(x)[0])
        last_price = float(history[-1])
        day_lower = last_price * 0.97
        day_upper = last_price * 1.03
        yhat = float(np.clip(yhat, day_lower, day_upper))
        yhat = float(np.clip(yhat, fixed_lower, fixed_upper))
        preds.append(yhat)
        history.append(yhat)

    return pd.DataFrame(
        {
            "date": future_dates,
            "predicted_price_original_scale": preds,
        }
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    loader = GoldDataLoader(data_path=BACKEND_DIR / "data" / "raw")
    raw_df = loader.load_financial_regression_data()
    raw_df = loader.clean_data(raw_df)

    # Raw dataset uses lowercase and spaces before feature engineering.
    close_col_raw = "gold close"
    date_col_raw = "Date" if "Date" in raw_df.columns else "date"

    analysis = analyze_price_scale(raw_df[close_col_raw])

    usd_transformer, annual_fit = infer_usd_transform(raw_df, close_col_raw, date_col_raw)

    raw_df["gold_close_usd_est"] = transform_to_usd(raw_df[close_col_raw].values, usd_transformer, annual_fit)

    engineer = FeatureEngineer(raw_df)
    df_features = engineer.create_all_features()
    data = loader.prepare_data_for_modeling(df_features)

    trainer = ModelTrainer(model_dir=MODEL_DIR)
    trainer.load_models()

    available_models = sorted(trainer.models.keys())
    if not available_models:
        raise RuntimeError("No trained models available.")

    # Use best available model by test RMSE for the primary output.
    model_rmse = []
    for m in available_models:
        rmse = float(trainer.metrics.get(m, {}).get("test", {}).get("rmse", np.inf))
        model_rmse.append((m, rmse))
    best_model = sorted(model_rmse, key=lambda x: x[1])[0][0]

    all_preds = []
    for model_id in available_models:
        df_pred = generate_2025_predictions(data, trainer, model_id)
        df_pred["predicted_price_usd"] = transform_to_usd(
            df_pred["predicted_price_original_scale"].values,
            usd_transformer,
            annual_fit,
        )
        df_pred["model_id"] = model_id
        all_preds.append(df_pred)

    pred_all = pd.concat(all_preds, ignore_index=True)
    pred_best = pred_all[pred_all["model_id"] == best_model].copy()

    pred_best_out = pred_best[["date", "predicted_price_original_scale", "predicted_price_usd"]].copy()
    pred_best_out.to_csv(OUT_DIR / "predictions_2025_best_model.csv", index=False)

    pred_all.to_csv(OUT_DIR / "predictions_2025_all_models.csv", index=False)

    # Visualization
    plt.figure(figsize=(14, 7))
    hist = raw_df[[date_col_raw, "gold_close_usd_est"]].copy()
    hist[date_col_raw] = pd.to_datetime(hist[date_col_raw])

    plt.plot(
        hist[date_col_raw],
        hist["gold_close_usd_est"],
        label="Historical (estimated USD/oz)",
        color="#1f77b4",
        linewidth=1.8,
    )

    for model_id in available_models:
        tmp = pred_all[pred_all["model_id"] == model_id]
        alpha = 0.85 if model_id == best_model else 0.45
        lw = 2.3 if model_id == best_model else 1.2
        plt.plot(
            tmp["date"],
            tmp["predicted_price_usd"],
            label=f"2025 forecast ({model_id})",
            linewidth=lw,
            alpha=alpha,
        )

    plt.title("Historical and 2025 Forecast Gold Prices (Estimated USD per oz)")
    plt.xlabel("Date")
    plt.ylabel("USD per troy ounce")
    plt.grid(alpha=0.2)
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUT_DIR / "historical_vs_2025_forecast_usd.png", dpi=150)
    plt.close()

    summary = {
        "scale_analysis": {
            "classification": analysis.classification,
            "reason": analysis.reason,
            "min": analysis.min_val,
            "max": analysis.max_val,
            "mean": analysis.mean_val,
            "std": analysis.std_val,
        },
        "annual_fit_mean_pct_error": float(annual_fit["pct_error"].mean()),
        "annual_fit_max_pct_error": float(annual_fit["pct_error"].max()),
        "best_model": best_model,
        "available_models": available_models,
        "output_files": {
            "best_model_csv": str(OUT_DIR / "predictions_2025_best_model.csv"),
            "all_models_csv": str(OUT_DIR / "predictions_2025_all_models.csv"),
            "plot": str(OUT_DIR / "historical_vs_2025_forecast_usd.png"),
        },
    }

    with open(OUT_DIR / "analysis_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\n=== SCALE ANALYSIS ===")
    print(f"Classification: {analysis.classification}")
    print(f"Reason: {analysis.reason}")
    print(f"Original close range: {analysis.min_val:.2f} .. {analysis.max_val:.2f}")
    print("\n=== TRANSFORMATION FIT ===")
    print(f"Mean annual mapping error: {annual_fit['pct_error'].mean():.2f}%")
    print(f"Max annual mapping error: {annual_fit['pct_error'].max():.2f}%")
    print("\n=== MODEL SELECTION ===")
    print(f"Available models: {available_models}")
    print(f"Best model (lowest test RMSE): {best_model}")
    print("\n=== OUTPUT ===")
    print(pred_best_out.head(10))
    print(f"\nSaved outputs under: {OUT_DIR}")


if __name__ == "__main__":
    main()
