"""
Feature Engineering Module
Creates ~80 features from raw data including technical indicators,
lag features, ratios, and rolling statistics
"""

import pandas as pd
import numpy as np
from typing import Tuple


class FeatureEngineer:
    """Generate features for gold price prediction"""
    
    def __init__(self, df):
        """Initialize with DataFrame"""
        self.df = df.copy()
        # Standardize column names to match expected format
        self.df.columns = self.df.columns.str.lower().str.replace(' ', '_')
        self.features_df = self.df.copy()
    
    def create_all_features(self):
        """
        Create all feature groups
        
        Returns:
            DataFrame with all features
        """
        print("Creating features...")
        
        # Technical indicators
        self._create_technical_indicators()
        
        # Cross-asset features
        self._create_cross_asset_features()
        
        # Lag features
        self._create_lag_features()
        
        # Rolling statistics
        self._create_rolling_statistics()
        
        # Time features
        self._create_time_features()
        
        # Remove any NaN created by feature engineering
        self.features_df = self.features_df.dropna()
        
        print(f"Total features created: {len(self.features_df.columns) - 1}")
        print(f"Rows after feature engineering: {len(self.features_df)}")
        
        return self.features_df
    
    def _create_technical_indicators(self):
        """Create technical indicators for gold"""
        
        # Simple Moving Averages
        for period in [10, 20, 50]:
            col_name = f'SMA_gold_{period}'
            if 'gold_close' in self.features_df.columns:
                self.features_df[col_name] = self.features_df['gold_close'].rolling(period).mean()
        
        # Exponential Moving Averages
        for period in [10, 20]:
            col_name = f'EMA_gold_{period}'
            if 'gold_close' in self.features_df.columns:
                self.features_df[col_name] = self.features_df['gold_close'].ewm(span=period, adjust=False).mean()
        
        # RSI (14-day)
        if 'gold_close' in self.features_df.columns:
            self.features_df['RSI_gold_14'] = self._calculate_rsi(
                self.features_df['gold_close'], period=14
            )
        
        # MACD
        if 'gold_close' in self.features_df.columns:
            macd_cols = self._calculate_macd(self.features_df['gold_close'])
            for col_name, values in macd_cols.items():
                self.features_df[col_name] = values
        
        # Bollinger Bands
        if 'gold_close' in self.features_df.columns:
            bb_cols = self._calculate_bollinger_bands(self.features_df['gold_close'])
            for col_name, values in bb_cols.items():
                self.features_df[col_name] = values
        
        # Returns and volatility
        if 'gold_close' in self.features_df.columns:
            self.features_df['Returns_gold'] = self.features_df['gold_close'].pct_change()
            self.features_df['Volatility_gold_20'] = self.features_df['Returns_gold'].rolling(20).std()
        
        print("✓ Technical indicators created")
    
    def _calculate_rsi(self, prices, period=14):
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_macd(self, prices, fast=12, slow=26, signal=9):
        """Calculate MACD"""
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        macd = ema_fast - ema_slow
        macd_signal = macd.ewm(span=signal, adjust=False).mean()
        
        return {
            'MACD_gold': macd,
            'MACD_Signal_gold': macd_signal,
            'MACD_Hist_gold': macd - macd_signal,
        }
    
    def _calculate_bollinger_bands(self, prices, period=20, num_std=2):
        """Calculate Bollinger Bands"""
        sma = prices.rolling(period).mean()
        std = prices.rolling(period).std()
        
        return {
            'BB_Upper_gold': sma + (std * num_std),
            'BB_Lower_gold': sma - (std * num_std),
            'BB_Middle_gold': sma,
            'BB_Width_gold': 2 * std * num_std,
        }
    
    def _create_cross_asset_features(self):
        """Create ratios and correlations between assets"""
        
        # Gold/Silver ratio
        if 'gold_close' in self.features_df.columns and 'silver_close' in self.features_df.columns:
            self.features_df['Ratio_Gold_Silver'] = self.features_df['gold_close'] / (
                self.features_df['silver_close'] + 1e-9
            )
        
        # Gold/Platinum ratio
        if 'gold_close' in self.features_df.columns and 'platinum_close' in self.features_df.columns:
            self.features_df['Ratio_Gold_Platinum'] = self.features_df['gold_close'] / (
                self.features_df['platinum_close'] + 1e-9
            )
        
        # Gold vs Oil ratio
        if 'gold_close' in self.features_df.columns and 'oil_close' in self.features_df.columns:
            self.features_df['Ratio_Gold_Oil'] = self.features_df['gold_close'] / (
                self.features_df['oil_close'] + 1e-9
            )
        
        # Rolling correlation: Gold vs S&P500
        if 'gold_close' in self.features_df.columns and 'sp500_close' in self.features_df.columns:
            self.features_df['Corr_Gold_SP500_20'] = self.features_df['gold_close'].rolling(20).corr(
                self.features_df['sp500_close']
            )
        
        # Gold spread (High - Low)
        if 'gold_high' in self.features_df.columns and 'gold_low' in self.features_df.columns:
            self.features_df['Spread_gold'] = self.features_df['gold_high'] - self.features_df['gold_low']
        
        print("✓ Cross-asset features created")
    
    def _create_lag_features(self):
        """Create lag features for gold and other assets"""
        
        # Gold lags
        for lag in [1, 2, 3, 5, 7]:
            if 'gold_close' in self.features_df.columns:
                self.features_df[f'Lag_gold_close_{lag}'] = self.features_df['gold_close'].shift(lag)
        
        # Silver, S&P500 lags
        for asset in ['silver', 'sp500']:
            close_col = f'{asset}_close'
            if close_col in self.features_df.columns:
                for lag in [1, 2, 3]:
                    self.features_df[f'Lag_{asset}_close_{lag}'] = self.features_df[close_col].shift(lag)
        
        print("✓ Lag features created")
    
    def _create_rolling_statistics(self):
        """Create rolling statistics for main assets"""
        
        for asset in ['gold', 'silver']:
            close_col = f'{asset}_close'
            if close_col in self.features_df.columns:
                for window in [7, 14, 30]:
                    # Rolling mean
                    self.features_df[f'Rolling_Mean_{asset}_{window}'] = (
                        self.features_df[close_col].rolling(window).mean()
                    )
                    
                    # Rolling std
                    self.features_df[f'Rolling_Std_{asset}_{window}'] = (
                        self.features_df[close_col].rolling(window).std()
                    )
                    
                    # Rolling min/max
                    self.features_df[f'Rolling_Min_{asset}_{window}'] = (
                        self.features_df[close_col].rolling(window).min()
                    )
                    self.features_df[f'Rolling_Max_{asset}_{window}'] = (
                        self.features_df[close_col].rolling(window).max()
                    )
        
        print("✓ Rolling statistics created")
    
    def _create_time_features(self):
        """Create time-based features"""
        
        if 'Date' in self.features_df.columns:
            # Extract time components
            self.features_df['Month'] = self.features_df['Date'].dt.month
            self.features_df['Quarter'] = self.features_df['Date'].dt.quarter
            self.features_df['DayOfWeek'] = self.features_df['Date'].dt.dayofweek
            self.features_df['DayOfYear'] = self.features_df['Date'].dt.dayofyear
            self.features_df['IsYearEnd'] = self.features_df['Date'].dt.is_year_end.astype(int)
            self.features_df['IsQuarterEnd'] = self.features_df['Date'].dt.is_quarter_end.astype(int)
            
            # Cyclical encoding (sin/cos) for Month
            self.features_df['Month_sin'] = np.sin(2 * np.pi * self.features_df['Month'] / 12)
            self.features_df['Month_cos'] = np.cos(2 * np.pi * self.features_df['Month'] / 12)
            
            # Cyclical encoding for DayOfWeek
            self.features_df['DayOfWeek_sin'] = np.sin(2 * np.pi * self.features_df['DayOfWeek'] / 7)
            self.features_df['DayOfWeek_cos'] = np.cos(2 * np.pi * self.features_df['DayOfWeek'] / 7)
            
            # Cyclical encoding for DayOfYear
            self.features_df['DayOfYear_sin'] = np.sin(2 * np.pi * self.features_df['DayOfYear'] / 365)
            self.features_df['DayOfYear_cos'] = np.cos(2 * np.pi * self.features_df['DayOfYear'] / 365)
        
        print("✓ Time features created")
    
    def get_feature_names(self, exclude_cols=None):
        """Get list of feature names (excluding target and date)"""
        if exclude_cols is None:
            exclude_cols = ['Date', 'date', 'gold_close', 'Close_gold']
        
        return [col for col in self.features_df.columns if col not in exclude_cols]
    
    def get_feature_categories(self):
        """Categorize features for analysis"""
        
        categories = {
            'Technical Indicators': [c for c in self.features_df.columns if any(
                x in c for x in ['SMA', 'EMA', 'RSI', 'MACD', 'BB', 'Volatility']
            )],
            'Cross-Asset': [c for c in self.features_df.columns if any(
                x in c for x in ['Ratio', 'Corr', 'Spread']
            )],
            'Lag Features': [c for c in self.features_df.columns if 'Lag' in c],
            'Rolling Statistics': [c for c in self.features_df.columns if 'Rolling' in c],
            'Time Features': [c for c in self.features_df.columns if any(
                x in c for x in ['Month', 'Quarter', 'DayOfWeek', 'DayOfYear', 'IsYear', 'IsQuarter']
            )],
            'Original Features': [c for c in self.features_df.columns if all(
                x not in c for x in ['SMA', 'EMA', 'RSI', 'MACD', 'BB', 'Volatility', 
                                      'Ratio', 'Corr', 'Spread', 'Lag', 'Rolling', 
                                      'Month', 'Quarter', 'DayOfWeek', 'Returns', 'Date']
            )],
        }
        
        return categories


def main():
    """Test feature engineering"""
    from data_loader import GoldDataLoader
    
    loader = GoldDataLoader()
    df = loader.load_financial_regression_data()
    df = loader.clean_data(df)
    
    engineer = FeatureEngineer(df)
    df_features = engineer.create_all_features()
    
    print(f"\nFinal shape: {df_features.shape}")
    print(f"\nFeature categories:")
    categories = engineer.get_feature_categories()
    for cat_name, features in categories.items():
        print(f"  {cat_name}: {len(features)}")


if __name__ == '__main__':
    main()
