import pandas as pd
import numpy as np
from sdv.evaluation.single_table import evaluate_quality
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, r2_score
from sklearn.model_selection import train_test_split

def get_fidelity_report(real_data, synthetic_data, metadata):
    try:
        report_score = evaluate_quality(real_data, synthetic_data, metadata)
        return report_score.get_score()
    except Exception as e:
        print(f"[Fidelity Error] {e}")
        return 0.0

def _prep_for_ml(df):
    """
    Private helper to convert complex types (Dates, Objects) 
    into a numerical format scikit-learn can digest.
    """
    df = df.copy()
    for col in df.columns:
        # 1. Handle Datetime columns
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            # Convert to seconds since epoch
            df[col] = pd.to_numeric(df[col], errors='coerce') / 10**9
        
        # 2. Handle Object/String columns that might be dates
        elif df[col].dtype == 'object':
            try:
                # Attempt conversion to datetime then to numeric
                temp_date = pd.to_datetime(df[col], errors='coerce')
                if not temp_date.isna().all():
                    df[col] = pd.to_numeric(temp_date, errors='coerce') / 10**9
            except:
                pass # Leave as object for get_dummies to handle
                
    # 3. Final cleanup: Fill any NaNs created during conversion
    return df.fillna(0)

def run_tstr_benchmark(real_data, synthetic_data, target_col):
    """
    Polymorphic TSTR Benchmark: Handles Datetimes, Categoricals, 
    and chooses between Classification/Regression.
    """
    try:
        # Clean and transform complex data types
        real_clean = _prep_for_ml(real_data)
        syn_clean = _prep_for_ml(synthetic_data)

        # Feature/Target Separation
        X_real = real_clean.drop(target_col, axis=1)
        y_real = real_clean[target_col]
        X_syn = syn_clean.drop(target_col, axis=1)
        y_syn = syn_clean[target_col]

        # 1. Detect Task Type
        is_regression = y_real.dtype == 'float64' or y_real.nunique() > 20

        # 2. Split REAL data (Holdout set)
        X_train_real, X_test_real, y_train_real, y_test_real = train_test_split(
            X_real, y_real, test_size=0.2, random_state=42
        )

        # 3. Robust Encoding & Alignment
        # Convert categories to dummies and ensure identical columns across sets
        X_syn_enc = pd.get_dummies(X_syn)
        X_test_real_enc = pd.get_dummies(X_test_real)
        
        # Align syn and test set
        X_syn_enc, X_test_real_enc = X_syn_enc.align(X_test_real_enc, join='left', axis=1, fill_value=0)
        
        # Align training set
        X_train_real_enc = pd.get_dummies(X_train_real)
        _, X_train_real_enc = X_syn_enc.align(X_train_real_enc, join='left', axis=1, fill_value=0)

        # 4. Model Selection
        if is_regression:
            model_syn = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
            model_real = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
            metric_fn = r2_score
            metric_name = "R² Score"
        else:
            model_syn = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
            model_real = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
            metric_fn = accuracy_score
            metric_name = "Accuracy"

        # 5. Execute TSTR (Train on Synthetic, Test on Real)
        model_syn.fit(X_syn_enc, y_syn)
        syn_preds = model_syn.predict(X_test_real_enc)
        tstr_score = metric_fn(y_test_real, syn_preds)

        # 6. Execute Baseline (Train on Real, Test on Real)
        model_real.fit(X_train_real_enc, y_train_real)
        real_preds = model_real.predict(X_test_real_enc)
        real_score = metric_fn(y_test_real, real_preds)

        # Calculate Gap (Real performance vs Synthetic performance)
        utility_gap = real_score - tstr_score
        
        return {
            "tstr_score": round(max(0, tstr_score), 3),
            "utility_gap": round(max(0, utility_gap), 3),
            "metric_type": metric_name,
            "is_viable": utility_gap < 0.2 if is_regression else utility_gap < 0.15
        }
    except Exception as e:
        print(f"[TSTR Benchmark Error] {e}")
        return {"tstr_score": 0.0, "utility_gap": 1.0, "is_viable": False}