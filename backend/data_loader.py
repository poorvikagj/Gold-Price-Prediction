"""
Data Loading and Preprocessing Module
Handles loading CSV data, cleaning, and basic validation
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path


class GoldDataLoader:
    """Load and preprocess gold price prediction data"""
    
    def __init__(self, data_path=None):
        """Initialize data loader with optional custom data path"""
        if data_path is None:
            self.data_path = Path(__file__).parent / 'data' / 'raw'
        else:
            self.data_path = Path(data_path)
        
        self.processed_path = Path(__file__).parent / 'data' / 'processed'
        self.processed_path.mkdir(exist_ok=True)
    
    def load_financial_regression_data(self, filename='financial_regression.csv'):
        """
        Load primary financial regression dataset (2010-2024)
        
        Args:
            filename: Name of CSV file in raw data directory
            
        Returns:
            df: Pandas DataFrame with loaded data
        """
        filepath = self.data_path / filename
        
        if not filepath.exists():
            raise FileNotFoundError(f"Data file not found: {filepath}")
        
        print(f"Loading data from {filepath}...")
        df = pd.read_csv(filepath)
        
        # Standardize column name: 'date' -> 'Date'
        if 'date' in df.columns and 'Date' not in df.columns:
            df.rename(columns={'date': 'Date'}, inplace=True)
        
        print(f"Loaded {len(df)} rows, {len(df.columns)} columns")
        print(f"Date range: {df['Date'].min()} to {df['Date'].max()}")
        
        return df
    
    def clean_data(self, df):
        """
        Clean and validate data
        
        Args:
            df: Raw DataFrame
            
        Returns:
            df: Cleaned DataFrame
        """
        # Convert Date to datetime
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
        
        # Sort by date
        df = df.sort_values('Date').reset_index(drop=True)
        
        # Handle missing values
        # Forward fill for economic indicators (stable variables)
        # Backward fill for remaining
        df = df.ffill().bfill()
        
        # Remove any remaining NaN
        initial_rows = len(df)
        df = df.dropna()
        
        if len(df) < initial_rows:
            print(f"Removed {initial_rows - len(df)} rows with NaN values")
        
        # Validate OHLC data integrity
        ohlc_cols = ['Open_gold', 'High_gold', 'Low_gold', 'Close_gold']
        for col in ohlc_cols:
            if col in df.columns:
                # Check if High >= Open, Low, Close
                if not all(df['High_gold'] >= df['Open_gold']):
                    print(f"Warning: Found High < Open in {col}")
        
        print(f"Data cleaning complete: {len(df)} rows retained")
        return df
    
    def get_feature_columns(self, df):
        """
        Identify and categorize feature columns
        
        Args:
            df: DataFrame
            
        Returns:
            dict: Column categories
        """
        columns = df.columns.tolist()
        
        categories = {
            'gold': [c for c in columns if 'gold' in c.lower()],
            'silver': [c for c in columns if 'silver' in c.lower()],
            'platinum': [c for c in columns if 'platinum' in c.lower()],
            'palladium': [c for c in columns if 'palladium' in c.lower()],
            'oil': [c for c in columns if 'oil' in c.lower()],
            'sp500': [c for c in columns if 'sp500' in c.lower() or 'S&P' in c],
            'nasdaq': [c for c in columns if 'nasdaq' in c.lower()],
            'currency': [c for c in columns if 'eur' in c.lower() or 'usd' in c.lower() or 'chf' in c.lower()],
            'economic': [c for c in columns if any(x in c.lower() for x in ['cpi', 'gdp', 'interest', 'rate'])],
        }
        
        # Remove empty categories
        categories = {k: v for k, v in categories.items() if v}
        
        return categories
    
    def get_data_statistics(self, df):
        """
        Get dataset statistics for frontend
        
        Args:
            df: DataFrame
            
        Returns:
            dict: Statistics
        """
        date_col = None
        if 'Date' in df.columns:
            date_col = 'Date'
        elif 'date' in df.columns:
            date_col = 'date'

        if date_col is not None:
            date_min = pd.to_datetime(df[date_col].min()).strftime('%Y-%m-%d')
            date_max = pd.to_datetime(df[date_col].max()).strftime('%Y-%m-%d')
        else:
            date_min = None
            date_max = None
        
        stats = {
            'rows': len(df),
            'columns': len(df.columns),
            'date_range': f"{date_min} to {date_max}",
            'date_min': date_min,
            'date_max': date_max,
            'features': [c for c in df.columns if c != 'Date'],
            'feature_categories': self.get_feature_columns(df),
            'missing_values': df.isnull().sum().to_dict(),
        }
        
        return stats
    
    def prepare_data_for_modeling(self, df, target_col='Close_gold', test_size=0.2):
        """
        Prepare data for ML modeling (features and target)
        
        Args:
            df: Cleaned DataFrame
            target_col: Target column name
            test_size: Test set proportion (chronological split)
            
        Returns:
            dict: X_train, X_test, y_train, y_test, dates_train, dates_test
        """
        # Separate date column - handle both 'Date' and 'date' (after feature engineering)
        date_col = 'Date' if 'Date' in df.columns else 'date'
        dates = df[date_col].values
        
        # Normalize target column name if needed
        if target_col not in df.columns:
            # Special case: 'Close_gold' -> 'gold_close'
            if target_col == 'Close_gold' and 'gold_close' in df.columns:
                target_col = 'gold_close'
            # Generic lowercase conversion
            elif target_col.lower() in df.columns:
                target_col = target_col.lower()
            # Try underscore/space swapping
            elif target_col.replace('_', '_').lower() in df.columns:
                target_col = target_col.replace('_', '_').lower()
            # If still not found, use the first numeric column as target (fallback)
            else:
                numeric_cols = df.select_dtypes(include=['float', 'int']).columns.tolist()
                if numeric_cols:
                    target_col = numeric_cols[-1]  # Use last numeric column as target
                    print(f"Target column not found. Using '{target_col}' instead.")
        
        # Get target and features
        y = df[target_col].values
        X = df.drop(columns=[date_col, target_col]).values
        feature_names = df.drop(columns=[date_col, target_col]).columns.tolist()
        
        # Chronological train/test split (not random!)
        split_idx = int(len(df) * (1 - test_size))
        
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        dates_train, dates_test = dates[:split_idx], dates[split_idx:]
        
        print(f"Train set: {len(X_train)} samples ({dates_train[0]} to {dates_train[-1]})")
        print(f"Test set: {len(X_test)} samples ({dates_test[0]} to {dates_test[-1]})")
        
        return {
            'X_train': X_train,
            'X_test': X_test,
            'y_train': y_train,
            'y_test': y_test,
            'dates_train': dates_train,
            'dates_test': dates_test,
            'feature_names': feature_names,
            'df_full': df,
        }


def main():
    """Test data loading"""
    loader = GoldDataLoader()
    df = loader.load_financial_regression_data()
    df = loader.clean_data(df)
    stats = loader.get_data_statistics(df)
    print("\nData Statistics:")
    print(f"Rows: {stats['rows']}")
    print(f"Columns: {stats['columns']}")
    print(f"Date Range: {stats['date_range']}")


if __name__ == '__main__':
    main()
