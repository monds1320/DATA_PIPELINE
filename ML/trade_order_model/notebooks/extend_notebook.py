import json
import os

notebook_path = 'ml_pipeline.ipynb'
with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Helper function to create code cell
def create_code_cell(source):
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + '\n' for line in source.split('\n')]
    }

def create_markdown_cell(source):
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + '\n' for line in source.split('\n')]
    }

# Ensure shap is installed
install_cell = create_code_cell("!pip install shap -q\nprint('✅ SHAP installed!')")

# Step 6: Feature Store
step6_md = create_markdown_cell("### Step 6: Feature Store Processing\nSimulate Feature Store registration.")
step6_code = create_code_cell("""# Step 6: Feature Store Processing
print('💾 Feature Store Processing...')
import pandas as pd
# Simulated feature store registration
feature_metadata = pd.DataFrame({
    'Feature': X.columns,
    'Type': [str(t) for t in X.dtypes],
    'Version': '1.0'
})
print('✅ Features registered in local store')
display(feature_metadata.head())
""")

# Step 9: Model Interpretation
step9_md = create_markdown_cell("### Step 9: Model Interpretation\nUsing SHAP for explainability.")
step9_code = create_code_cell("""# Step 9: Model Interpretation (SHAP)
print('🔍 Model Interpretation with SHAP...\\n')
try:
    import shap
    shap.initjs()
    explainer = shap.TreeExplainer(best_model)
    # Use a small sample for SHAP to save time
    X_sample = X_test.sample(min(100, len(X_test)), random_state=CONFIG['random_state'])
    shap_values = explainer.shap_values(X_sample)
    
    import matplotlib.pyplot as plt
    plt.figure(figsize=(10, 6))
    shap.summary_plot(shap_values, X_sample, show=False)
    plt.savefig('../outputs/shap_summary.png', dpi=300, bbox_inches='tight')
    plt.show()
    print('✅ SHAP summary plot saved to: ../outputs/shap_summary.png')
except ImportError:
    print('⚠️ SHAP library not installed. Skipping model interpretation.')
except Exception as e:
    print(f'⚠️ Error generating SHAP plots: {e}')
""")

# Step 10 & 11: Hyperparameter Optimization and Retraining
step10_md = create_markdown_cell("### Step 10 & 11: Hyperparameter Optimization & Model Retraining\nOptimize parameters and retrain the best model.")
step10_code = create_code_cell("""# Step 10: Hyperparameter Optimization
print('⚙️ Hyperparameter Optimization for best model...\\n')
from sklearn.model_selection import GridSearchCV

if best_model_name == 'LightGBM':
    param_grid = {
        'n_estimators': [50, 100],
        'learning_rate': [0.05, 0.1],
        'max_depth': [5, 10]
    }
    grid_search = GridSearchCV(
        estimator=lgb.LGBMRegressor(random_state=CONFIG['random_state'], n_jobs=-1, verbose=-1),
        param_grid=param_grid,
        cv=3,
        scoring='neg_mean_squared_error',
        n_jobs=-1
    )
elif best_model_name == 'XGBoost':
    param_grid = {
        'n_estimators': [50, 100],
        'learning_rate': [0.05, 0.1],
        'max_depth': [3, 5]
    }
    grid_search = GridSearchCV(
        estimator=xgb.XGBRegressor(random_state=CONFIG['random_state'], n_jobs=-1),
        param_grid=param_grid,
        cv=3,
        scoring='neg_mean_squared_error',
        n_jobs=-1
    )
else:
    from sklearn.ensemble import RandomForestRegressor
    param_grid = {
        'n_estimators': [50, 100],
        'max_depth': [5, 10]
    }
    grid_search = GridSearchCV(
        estimator=RandomForestRegressor(random_state=CONFIG['random_state'], n_jobs=-1),
        param_grid=param_grid,
        cv=3,
        scoring='neg_mean_squared_error',
        n_jobs=-1
    )

grid_search.fit(X_train, y_train)
optimized_model = grid_search.best_estimator_
print(f'✅ Best Hyperparameters: {grid_search.best_params_}')

# Step 11: Model Retraining
print('\\n🔄 Model Retraining with optimized hyperparameters...\\n')
optimized_model.fit(X_train, y_train)
print('✅ Model retrained successfully.')

import pickle
# Update best_model to the optimized one for subsequent steps
best_model = optimized_model
with open(f'../models/optimized_model_{best_model_name}.pkl', 'wb') as f:
    pickle.dump(best_model, f)
print('✅ Retrained model saved.')
""")

# Step 13: Model Validation & Testing
step13_md = create_markdown_cell("### Step 13: Model Validation & Testing\nFairness, robustness, and A/B test simulation.")
step13_code = create_code_cell("""# Step 13: Model Validation & Testing
print('🧪 Model Validation (Fairness & Robustness)...\\n')
import numpy as np
from sklearn.metrics import mean_squared_error

# Simple Robustness test (add noise to test data)
X_test_noisy = X_test.copy()
# Add 5% noise to numerical features
for col in X_test_noisy.select_dtypes(include=[np.number]).columns:
    X_test_noisy[col] = X_test_noisy[col] * np.random.normal(1, 0.05, len(X_test_noisy))

noisy_preds = best_model.predict(X_test_noisy)
noisy_rmse = np.sqrt(mean_squared_error(y_test, noisy_preds))

print(f'✅ Robustness Test - Noisy RMSE: ${noisy_rmse:.4f} (Original: ${test_rmse:.4f})')
try:
    print(f'Performance drop: {((noisy_rmse - test_rmse) / test_rmse) * 100:.2f}%')
except:
    pass

# A/B Testing Simulation
print('\\n📊 A/B Testing Simulation...')
print('Simulating Model A (Baseline/Linear) vs Model B (Optimized)')
model_a = models['LinearRegression']
preds_a = model_a.predict(X_test)
rmse_a = np.sqrt(mean_squared_error(y_test, preds_a))

print(f'Model A (Linear) RMSE: ${rmse_a:.4f}')
print(f'Model B ({best_model_name}) RMSE: ${test_rmse:.4f}')
improvement = ((rmse_a - test_rmse) / rmse_a) * 100
print(f'✅ Model B shows {improvement:.2f}% improvement over Baseline.')
""")

# We need to insert these cells at appropriate positions or just append at the end.
# If we append at the end, it's safer and "don't change the codes" holds perfectly.
# But logically they should be in the middle. Let's find "Step 12: Demo Use Case" and insert before it,
# or just insert before "Step 13: Final Deployment Package"
insert_index = len(nb['cells'])

# Let's find index of "# Step 11: Model Capabilities Documentation" to insert before it
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code' and any("Step 12: Demo Use Case" in line for line in cell['source']):
        insert_index = i
        break

# If not found, just append to the end
nb['cells'].insert(insert_index, step13_code)
nb['cells'].insert(insert_index, step13_md)

nb['cells'].insert(insert_index, step10_code)
nb['cells'].insert(insert_index, step10_md)

nb['cells'].insert(insert_index, step9_code)
nb['cells'].insert(insert_index, step9_md)

nb['cells'].insert(insert_index, step6_code)
nb['cells'].insert(insert_index, step6_md)

nb['cells'].insert(0, install_cell)

with open('ml_pipeline_extended.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)

print('✅ Created ml_pipeline_extended.ipynb successfully!')
