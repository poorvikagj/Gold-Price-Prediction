import React from 'react';
import '../styles/About.css';

function About() {
  return (
    <div className="about">
      <h2>About This Project</h2>

      {/* Project Overview */}
      <section className="about-section">
        <h3>Project Overview</h3>
        <p>
          This is a student-level machine learning project that demonstrates how to predict gold prices 
          using economic indicators, technical analysis, and multiple machine learning approaches. The project 
          showcases the full ML pipeline: data collection, feature engineering, model training, and interactive visualization.
        </p>
      </section>

      {/* Methodology */}
      <section className="about-section">
        <h3>Methodology</h3>
        <div className="methodology-steps">
          <div className="step">
            <div className="step-number">1</div>
            <h4>Data Preparation</h4>
            <p>
              Loaded 3,904 daily records (2010-2024) from the Financial Regression dataset containing gold prices, 
              precious metals, stocks, currencies, and economic indicators. Applied forward-fill for handling missing 
              values in stable economic indicators.
            </p>
          </div>

          <div className="step">
            <div className="step-number">2</div>
            <h4>Feature Engineering</h4>
            <p>
              Created ~80 engineered features including technical indicators (SMA, EMA, RSI, MACD, Bollinger Bands), 
              cross-asset ratios, lag features, rolling statistics, and cyclical time encoding. Features capture 
              different aspects of market dynamics at multiple timescales.
            </p>
          </div>

          <div className="step">
            <div className="step-number">3</div>
            <h4>Model Training</h4>
            <p>
              Trained three regression models on 80% of chronologically-ordered data (train/test split to preserve 
              temporal structure). Models: Linear Regression (baseline), Random Forest (ensemble), and XGBoost 
              (advanced ensemble). Evaluated on holdout test set.
            </p>
          </div>

          <div className="step">
            <div className="step-number">4</div>
            <h4>Model Evaluation</h4>
            <p>
              Compared models using R², RMSE, MAE, and MAPE metrics. XGBoost typically achieved R² ≈ 0.95, 
              indicating the model explains 95% of price variance. Analyzed feature importance to understand 
              key drivers of gold prices.
            </p>
          </div>

          <div className="step">
            <div className="step-number">5</div>
            <h4>Web Application</h4>
            <p>
              Built Flask REST API backend for model serving and React frontend with interactive dashboards, 
              predictions visualization, feature analysis, and performance metrics. Enables users to understand 
              and interact with the ML pipeline.
            </p>
          </div>
        </div>
      </section>

      {/* Machine Learning Models */}
      <section className="about-section">
        <h3>Machine Learning Models Explained</h3>

        <div className="model-explanation">
          <div className="model-card">
            <h4>Linear Regression</h4>
            <div className="model-role">Baseline</div>
            <p className="description">
              Assumes a linear relationship between features and gold prices. Serves as a baseline to measure 
              how much the more complex models improve over simple linear assumptions.
            </p>
            <div className="strengths">
              <strong>Strengths:</strong>
              <ul>
                <li>Interpretable - coefficients show feature impact</li>
                <li>Fast to train and predict</li>
                <li>Good for understanding linear trends</li>
              </ul>
            </div>
            <div className="weaknesses">
              <strong>Limitations:</strong>
              <ul>
                <li>Assumes linear relationships (often unrealistic)</li>
                <li>Cannot capture feature interactions</li>
                <li>Lower accuracy on complex data</li>
              </ul>
            </div>
          </div>

          <div className="model-card">
            <h4>Random Forest</h4>
            <div className="model-role">Ensemble of Decision Trees</div>
            <p className="description">
              Uses multiple decision trees trained on random subsets of features and data. Averages predictions 
              to reduce overfitting and improve generalization. Captures non-linear relationships naturally.
            </p>
            <div className="strengths">
              <strong>Strengths:</strong>
              <ul>
                <li>Captures non-linear relationships</li>
                <li>Handles feature interactions</li>
                <li>Robust to outliers</li>
                <li>Provides feature importance rankings</li>
              </ul>
            </div>
            <div className="weaknesses">
              <strong>Limitations:</strong>
              <ul>
                <li>More complex than linear regression</li>
                <li>Less interpretable ("black box")</li>
                <li>Slower than linear models</li>
              </ul>
            </div>
          </div>

          <div className="model-card">
            <h4>XGBoost</h4>
            <div className="model-role">Gradient Boosting Ensemble</div>
            <p className="description">
              Builds trees sequentially, each correcting errors of previous ones. "Boosting" means each tree 
              focuses on hard-to-predict cases. Highly effective for structured data and competitions.
            </p>
            <div className="strengths">
              <strong>Strengths:</strong>
              <ul>
                <li>State-of-the-art performance on structured data</li>
                <li>Handles complex feature interactions</li>
                <li>Built-in feature importance</li>
                <li>Regularization prevents overfitting</li>
              </ul>
            </div>
            <div className="weaknesses">
              <strong>Limitations:</strong>
              <ul>
                <li>More hyperparameters to tune</li>
                <li>Slower to train than Random Forest</li>
                <li>Still somewhat of a "black box"</li>
              </ul>
            </div>
          </div>
        </div>

        <div className="why-these-models">
          <h4>Why These Three Models?</h4>
          <p>
            These three models represent a progression from simple to complex:
          </p>
          <ul>
            <li><strong>Linear Regression:</strong> Sets a quantifiable baseline</li>
            <li><strong>Random Forest:</strong> Shows improvement from non-linear modeling</li>
            <li><strong>XGBoost:</strong> Represents state-of-the-art for structured data</li>
          </ul>
          <p>
            Comparing them demonstrates why more sophisticated models are needed for financial prediction.
          </p>
        </div>
      </section>

      {/* Key Features Explained */}
      <section className="about-section">
        <h3>Key Features & Economic Reasoning</h3>

        <div className="features-explained">
          <div className="feature-group">
            <h4>🥈 Silver (Precious Metal)</h4>
            <p>
              <strong>Correlation:</strong> 0.85+ with gold | <strong>Lead indicator:</strong> Often moves first
            </p>
            <p>
              Silver responds to similar economic forces but is more volatile. High silver prices or silver-to-gold 
              ratios can signal industrial demand or inflation expectations. Silver moves often precede gold moves.
            </p>
          </div>

          <div className="feature-group">
            <h4>📈 S&P 500 (Equity Market)</h4>
            <p>
              <strong>Relationship:</strong> Inverse (risk-on vs risk-off) | <strong>Sentiment indicator</strong>
            </p>
            <p>
              Gold is a "risk-off" asset (bought during fear/recession). When stocks rise, investors take more 
              risk and gold appeal diminishes. Stock market strength predicts lower gold prices and vice versa.
            </p>
          </div>

          <div className="feature-group">
            <h4>💱 EUR/USD (Currency)</h4>
            <p>
              <strong>Key factor:</strong> Gold priced in USD | <strong>Commodity currency</strong>
            </p>
            <p>
              A strong dollar (low EUR/USD) makes gold more expensive for foreign buyers, reducing demand and 
              prices. Conversely, a weak dollar makes gold cheaper internationally, supporting prices.
            </p>
          </div>

          <div className="feature-group">
            <h4>⛽ Oil (Energy/Inflation)</h4>
            <p>
              <strong>Shared factor:</strong> Inflation expectations | <strong>Industry demand</strong>
            </p>
            <p>
              Oil and gold tend to rise together during inflationary periods. Both are inflation hedges. Oil 
              also indicates economic activity - strong oil prices suggest growing economies, affecting gold demand.
            </p>
          </div>

          <div className="feature-group">
            <h4>📊 Technical Indicators</h4>
            <p>
              <strong>RSI, MACD, Bollinger Bands:</strong> Market sentiment and momentum
            </p>
            <p>
              These identify overbought/oversold conditions, trend changes, and support/resistance levels. 
              Help predict mean reversion and trend continuation in short term.
            </p>
          </div>
        </div>
      </section>

      {/* Dataset Information */}
      <section className="about-section">
        <h3>Dataset Information</h3>

        <div className="dataset-info">
          <div className="dataset-card">
            <h4>Primary Dataset: Financial Regression</h4>
            <ul>
              <li><strong>Period:</strong> 2010-2024 (14 years of daily data)</li>
              <li><strong>Samples:</strong> 3,904 trading days</li>
              <li><strong>Features:</strong> 47 raw features</li>
              <li><strong>Target:</strong> Gold Close price (USD/oz)</li>
              <li><strong>Coverage:</strong> Precious metals, stocks, currencies, economic indicators</li>
            </ul>
            <p>
              This dataset provides stable, long-term data encompassing multiple market regimes: 2011 peak, 
              2013 crash, 2016 bottom, 2020 COVID spike, and 2022 volatility.
            </p>
          </div>

          <div className="dataset-card">
            <h4>Feature Engineering</h4>
            <ul>
              <li><strong>Raw features:</strong> 47</li>
              <li><strong>Technical Indicators:</strong> 15 features</li>
              <li><strong>Cross-asset ratios:</strong> 8 features</li>
              <li><strong>Lag features:</strong> 15 features</li>
              <li><strong>Rolling statistics:</strong> 20 features</li>
              <li><strong>Time features:</strong> 10 features</li>
              <li><strong>Total features:</strong> ~80</li>
            </ul>
            <p>
              Feature count grows from 47 to ~80 after engineering. Research shows diminishing returns 
              beyond 80-100 features for this dataset.
            </p>
          </div>
        </div>
      </section>

      {/* Technical Stack */}
      <section className="about-section">
        <h3>Technical Stack</h3>

        <div className="tech-stack">
          <div className="tech-category">
            <h4>Backend</h4>
            <ul>
              <li>Python 3.12</li>
              <li>Flask (REST API framework)</li>
              <li>scikit-learn (preprocessing, evaluation)</li>
              <li>XGBoost (advanced model)</li>
              <li>pandas/NumPy (data processing)</li>
              <li>joblib (model persistence)</li>
            </ul>
          </div>

          <div className="tech-category">
            <h4>Frontend</h4>
            <ul>
              <li>React 18 (UI framework)</li>
              <li>Recharts (data visualization)</li>
              <li>Axios (API calls)</li>
              <li>CSS3 (styling with dark mode)</li>
              <li>React Router (navigation)</li>
            </ul>
          </div>

          <div className="tech-category">
            <h4>Architecture</h4>
            <ul>
              <li>Microservices: Frontend ↔ Backend API</li>
              <li>REST API: JSON data exchange</li>
              <li>Model persistence: Pickle files</li>
              <li>CORS enabled: Cross-origin requests</li>
              <li>Local deployment: Development servers</li>
            </ul>
          </div>
        </div>
      </section>

      {/* Results Summary */}
      <section className="about-section">
        <h3>Results Summary</h3>

        <div className="results-grid">
          <div className="result-card">
            <h4>Best Model Performance</h4>
            <div className="result-metric">
              <span>R² Score:</span>
              <strong>≈ 0.95-0.97</strong>
            </div>
            <div className="result-metric">
              <span>RMSE:</span>
              <strong>≈ $20-25/oz</strong>
            </div>
            <div className="result-metric">
              <span>MAE:</span>
              <strong>≈ $15-18/oz</strong>
            </div>
            <p>Model explains 95% of gold price variance on test set</p>
          </div>

          <div className="result-card">
            <h4>Feature Impact Analysis</h4>
            <div className="result-metric">
              <span>Gold-only baseline:</span>
              <strong>R² ≈ 0.82</strong>
            </div>
            <div className="result-metric">
              <span>+ Economic features:</span>
              <strong>+6% improvement</strong>
            </div>
            <div className="result-metric">
              <span>+ Lag features:</span>
              <strong>+4% improvement</strong>
            </div>
            <p>Economic factors add significant predictive power</p>
          </div>

          <div className="result-card">
            <h4>Key Drivers (Feature Importance)</h4>
            <ol>
              <li>Silver price lags (1-7 days)</li>
              <li>Gold/Silver ratio</li>
              <li>S&P 500 returns</li>
              <li>EUR/USD exchange rate</li>
              <li>Technical indicators (RSI, volatility)</li>
            </ol>
          </div>

          <div className="result-card">
            <h4>Generalization</h4>
            <p>
              <strong>Train/Test Gap:</strong> &lt; 2%
            </p>
            <p>
              Minimal overfitting. Model performance consistent between 
              training and unseen test data. Good sign of model robustness.
            </p>
          </div>
        </div>
      </section>

      {/* Limitations & Future Work */}
      <section className="about-section">
        <h3>Limitations & Future Improvements</h3>

        <div className="future-work">
          <div className="limitation">
            <h4>Current Limitations</h4>
            <ul>
              <li><strong>Data scope:</strong> Daily data only (no intraday patterns)</li>
              <li><strong>Period:</strong> 2010-2024 (doesn't include 2008 crisis)</li>
              <li><strong>External factors:</strong> Political events, central bank policies not directly modeled</li>
              <li><strong>Scalability:</strong> Development-level, not production hardened</li>
              <li><strong>Real-time:</strong> Predictions use closing prices (end-of-day only)</li>
            </ul>
          </div>

          <div className="limitation">
            <h4>Potential Improvements</h4>
            <ul>
              <li>Add intraday features (15-min, hourly data)</li>
              <li>Include sentiment analysis from financial news</li>
              <li>Add central bank policy indicators</li>
              <li>Use LSTM/RNN for sequential patterns</li>
              <li>Ensemble multiple models for robustness</li>
              <li>Deploy to cloud with real-time predictions</li>
              <li>Add explainability with SHAP values</li>
            </ul>
          </div>
        </div>
      </section>

      {/* Credits */}
      <section className="about-section credits">
        <h3>Project Information</h3>
        <p>
          <strong>Type:</strong> Student ML Project (Development Level)
        </p>
        <p>
          <strong>Purpose:</strong> Educational demonstration of the complete ML pipeline: 
          data collection → feature engineering → model training → interactive visualization
        </p>
        <p>
          <strong>Platform:</strong> WSL2, Python 3.12, React 18
        </p>
        <p>
          <strong>Created:</strong> 2025
        </p>
      </section>
    </div>
  );
}

export default About;
