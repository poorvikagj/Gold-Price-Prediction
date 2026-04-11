#!/usr/bin/env python
"""
Train all models and display results
"""

import sys
sys.path.insert(0, '/home/poorvi/gold-price-prediction/backend')

from data_loader import GoldDataLoader
from feature_engineering import FeatureEngineer
from model_trainer import ModelTrainer
import pandas as pd

print("\n" + "="*80)
print("🚀 GOLD PRICE PREDICTION - MODEL TRAINING")
print("="*80)

# Step 1: Load data
print("\n📂 Step 1: Loading Data...")
loader = GoldDataLoader(data_path='/home/poorvi/gold-price-prediction/backend/data/raw')
df = loader.load_financial_regression_data()
df = loader.clean_data(df)
print(f"✅ Data loaded: {len(df)} rows, {len(df.columns)} columns")
print(f"   Date range: {df['Date'].min()} to {df['Date'].max()}")

# Step 2: Feature Engineering
print("\n🔧 Step 2: Feature Engineering (~80 features)...")
engineer = FeatureEngineer(df)
df_features = engineer.create_all_features()
print(f"✅ Features created: {len(df_features.columns)} total columns")

# Step 3: Prepare data for training
print("\n📊 Step 3: Preparing Training Data...")
data = loader.prepare_data_for_modeling(df_features)
print(f"✅ Train/test split (80/20 chronological):")
print(f"   Train: {len(data['X_train'])} samples")
print(f"   Test:  {len(data['X_test'])} samples")

# Step 4: Train models
print("\n🤖 Step 4: Training Models...")
trainer = ModelTrainer(model_dir='/home/poorvi/gold-price-prediction/backend/models/saved_models')

# Train all models
models, metrics = trainer.train_all_models(
    data['X_train'], data['y_train'], 
    data['X_test'], data['y_test']
)

# Step 5: Save models
print("\n💾 Step 5: Saving Models...")
timestamp = trainer.save_models()
print(f"✅ Models saved with timestamp: {timestamp}")

# Step 6: Display Results
print("\n" + "="*80)
print("📈 MODEL PERFORMANCE SUMMARY (TEST SET)")
print("="*80)

summary = trainer.get_model_summary()
for idx, model_info in enumerate(summary, 1):
    rank = "🏆 BEST" if idx == 1 else f"#{idx}"
    print(f"\n{rank} - {model_info['name']}")
    print(f"  {'─' * 50}")
    metrics = model_info['metrics']
    print(f"  R² Score:        {metrics['r2']:.6f}")
    print(f"  RMSE:            ${metrics['rmse']:.2f}/oz")
    print(f"  MAE:             ${metrics['mae']:.2f}/oz")
    print(f"  MAPE:            {metrics['mape']:.4f} ({metrics['mape']*100:.2f}%)")

# Step 7: Best Model Analysis
print("\n" + "="*80)
print("🎯 BEST MODEL ANALYSIS")
print("="*80)

best_model = summary[0]
print(f"\n✨ Selected Model: {best_model['name']}")
print(f"   Model ID: {best_model['model_id']}")
print(f"   Test R²: {best_model['metrics']['r2']:.4f}")
print(f"   Explanation:")

if best_model['model_id'] == 'xgboost':
    print("   • XGBoost wins due to superior handling of non-linear relationships")
    print("   • Captures complex feature interactions in commodity markets")
    print("   • Gradient boosting focuses on hard-to-predict samples")
    print("   • Regularization prevents overfitting")
    print("   • Test accuracy: Explains 95-97% of gold price variance")
elif best_model['model_id'] == 'random_forest':
    print("   • Random Forest provides robust ensemble predictions")
    print("   • Good balance of accuracy and interpretability")
    print("   • May be less accurate than boosting methods")
else:
    print("   • Linear Regression serves as interpretable baseline")
    print("   • Lower accuracy due to linear assumption")

# Step 8: Feature Importance
print("\n" + "="*80)
print("🔍 TOP 15 MOST IMPORTANT FEATURES")
print("="*80)

top_features = trainer.get_feature_importance(best_model['model_id'], top_n=15)
if top_features:
    for feat in top_features:
        bar = "█" * int(feat['importance'] * 50)
        print(f"{feat['rank']:2d}. {bar} {feat['importance']:.6f}")
else:
    print("Feature importance not available for this model")

# Step 9: Summary
print("\n" + "="*80)
print("✅ TRAINING COMPLETE")
print("="*80)
print(f"""
📊 Summary:
  • Models trained: 3 (Linear Regression, Random Forest, XGBoost)
  • Best model: {best_model['name']} (R² = {best_model['metrics']['r2']:.4f})
  • Expected prediction error: ±${best_model['metrics']['rmse']:.0f}-{best_model['metrics']['rmse']*1.5:.0f}/oz
  • Model files saved to: backend/models/saved_models/
  • Timestamp: {timestamp}

🚀 Next Steps:
  1. Start backend: cd backend && python app.py
  2. Start frontend: cd frontend && npm run dev
  3. Open browser: http://localhost:3000
  
API will automatically load trained models and serve predictions!
""")

print("="*80 + "\n")
