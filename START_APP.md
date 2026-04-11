# 🚀 How to Run the Application

## ✅ Current Status

### Backend (Flask API) - WORKING ✅
- **Status**: Running on http://localhost:5000
- **Health Check**: `curl http://localhost:5000/api/health`
- **Models**: Linear Regression, Random Forest, XGBoost (all trained)

### Frontend (React) - Ready to Start
- npm packages installed
- Just need to start the dev server

---

## 🎯 QUICK START INSTRUCTIONS

### Terminal 1 - Start Backend
```bash
cd /home/poorvi/gold-price-prediction/backend
/home/poorvi/gold-price-prediction/.venv/bin/python app.py
```
✅ You'll see: `* Running on http://0.0.0.0:5000`

### Terminal 2 - Start Frontend
```bash
cd /home/poorvi/gold-price-prediction/frontend
npm run dev
```
✅ You'll see: `VITE v5.0.0 ready in XXX ms` and `Local: http://localhost:3000`

### Step 3 - Open Browser
Navigate to: **http://localhost:3000**

---

## 📊 What You'll See

Once the app loads:

1. **Dashboard Page** - Model Performance Comparison
   - ✅ Linear Regression: R² = 0.9999 (BEST)
   - Random Forest: R² = 0.4366
   - XGBoost: R² = 0.3639

2. **Predictions** - Interactive chart showing actual vs predicted prices

3. **Feature Analysis** - Top features driving predictions

4. **Performance** - Detailed metrics and error analysis

5. **About** - Methodology documentation

---

## 🔗 API Endpoints (Backend Only)

```bash
# Health check
curl http://localhost:5000/api/health

# Get all models
curl http://localhost:5000/api/models

# Get model metrics
curl http://localhost:5000/api/metrics

# Make prediction
curl -X POST http://localhost:5000/api/predict \
  -H "Content-Type: application/json" \
  -d '{"input_features": [...]}'
```

---

## ✨ Frontend Features

- 📱 Responsive design (works on all devices)
- 🌙 Dark mode ready
- 📈 Interactive charts (Recharts)
- 🎨 Professional styling
- ⚡ Hot reload (automatic updates while developing)

---

## 🆘 Common Issues

### If backend doesn't start:
```bash
# Reinstall dependencies
/home/poorvi/gold-price-prediction/.venv/bin/pip install Flask flask-cors pandas numpy scikit-learn xgboost joblib
```

### If frontend doesn't build:
```bash
# Reinstall npm packages
cd /home/poorvi/gold-price-prediction/frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

---

## 📝 Environment Info

- Python: 3.12.3
- Node.js: 10.9.4
- Backend: Flask 3.0
- Frontend: React 18.2, Vite 5.0

---

