import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

def calculate_membership_leakage(real_data: pd.DataFrame, synthetic_data: pd.DataFrame):
    """
    Simulates a Membership Inference Attack (MIA).
    If a classifier can easily tell 'Real' from 'Synthetic', 
    the privacy risk is high.
    """
    # 1. Label the data
    real_df = real_data.copy()
    syn_df = synthetic_data.copy()
    
    real_df['target'] = 1  # Real data
    syn_df['target'] = 0   # Synthetic data
    
    # 2. Create a balanced attack set
    combined = pd.concat([real_df, syn_df]).sample(frac=1).reset_index(drop=True)
    X = combined.drop('target', axis=1)
    y = combined['target']
    
    # Handle categorical variables for the classifier
    X = pd.get_dummies(X)
    
    # 3. Train the "Attacker" model
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3)
    attacker = RandomForestClassifier(n_estimators=100, max_depth=10)
    attacker.fit(X_train, y_train)
    
    # 4. Calculate Risk Score
    # An accuracy of 0.50 means the attacker is just guessing (Safe).
    # An accuracy of 1.00 means the synthetic data perfectly mirrors real records (Unsafe).
    predictions = attacker.predict(X_test)
    attack_accuracy = accuracy_score(y_test, predictions)
    
    # Normalized Risk Score: 0 (Safe) to 1 (Leaked)
    risk_score = max(0, (attack_accuracy - 0.5) * 2)
    return round(risk_score, 2)