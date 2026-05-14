import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import pickle
import os

def train_and_save_model():
    # 1. Generate Synthetic Data for Soil Health Score
    # Features: pH, EC, OC, N, P, K
    # Target: Health Score (0-100)
    import numpy as np
    np.random.seed(42)
    
    n_samples = 1000
    ph = np.random.uniform(4.0, 10.0, n_samples)
    ec = np.random.uniform(0.5, 8.0, n_samples)
    oc = np.random.uniform(0.1, 1.5, n_samples)
    n = np.random.uniform(100, 400, n_samples)
    p = np.random.uniform(5, 50, n_samples)
    k = np.random.uniform(50, 300, n_samples)
    
    # Simple heuristic to calculate target "true" health score
    # Optimal: pH 6.5-7.5, EC < 2, OC > 0.8, N > 280, P > 22, K > 140
    scores = []
    for i in range(n_samples):
        score = 100
        if ph[i] > 8.0 or ph[i] < 6.0: score -= 20
        if ec[i] > 4.0: score -= 15
        if oc[i] < 0.5: score -= 15
        if n[i] < 280: score -= 10
        if p[i] < 22: score -= 10
        if k[i] < 140: score -= 10
        
        # Add some noise
        score += np.random.normal(0, 3)
        scores.append(max(0, min(100, score)))
        
    df = pd.DataFrame({
        'ph': ph, 'ec': ec, 'oc': oc, 'n': n, 'p': p, 'k': k, 'score': scores
    })
    
    X = df[['ph', 'ec', 'oc', 'n', 'p', 'k']]
    y = df['score']
    
    # 2. Train Random Forest
    rf = RandomForestRegressor(n_estimators=100, random_state=42)
    rf.fit(X, y)
    
    # 3. Save Model
    os.makedirs(os.path.dirname(os.path.abspath(__file__)), exist_ok=True)
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rf_model.pkl'), 'wb') as f:
        pickle.dump(rf, f)
        
    print("Model trained and saved to rf_model.pkl")

def load_model():
    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rf_model.pkl')
    if not os.path.exists(model_path):
        train_and_save_model()
        
    with open(model_path, 'rb') as f:
        return pickle.load(f)

if __name__ == "__main__":
    train_and_save_model()
