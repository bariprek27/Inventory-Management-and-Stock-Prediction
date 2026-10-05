"""
services/forecasting_service.py
Forecasting engine using Scikit-learn (Linear Regression) and Moving Average:
- Retrieves daily product sales history
- Imputes zero-sales days for accurate demand patterns
- Generates predicted daily demand
- Calculates Estimated Days Until Stock-Out
- Generates intelligent Reorder Recommendations
- Records forecasts in MySQL
"""
import pandas as pd
import numpy as np
from datetime import date, datetime, timedelta
from typing import Dict, Any, List, Optional
from sklearn.linear_model import LinearRegression

from database.queries import execute_read, execute_write

class ForecastingService:
    @staticmethod
    def get_product_daily_sales(product_id: int) -> pd.DataFrame:
        """Fetch historical daily sales for a single product."""
        sql = """
            SELECT s.sale_date, SUM(si.quantity) as quantity
            FROM sales s
            JOIN sale_items si ON s.sale_id = si.sale_id
            WHERE si.product_id = %s
            GROUP BY s.sale_date
            ORDER BY s.sale_date ASC
        """
        rows = execute_read(sql, (product_id,))
        if not rows:
            return pd.DataFrame(columns=['date', 'quantity'])
        df = pd.DataFrame(rows)
        df['sale_date'] = pd.to_datetime(df['sale_date'])
        
        # Fill missing days in range with 0 to accurately reflect zero-demand days
        min_date = df['sale_date'].min()
        max_date = df['sale_date'].max()
        all_days = pd.date_range(start=min_date, end=max_date, freq='D')
        df = df.set_index('sale_date').reindex(all_days, fill_value=0).rename_axis('sale_date').reset_index()
        df.rename(columns={'sale_date': 'date'}, inplace=True)
        return df

    @classmethod
    def predict_product_demand(
        cls, 
        product_id: int, 
        method: str = "Linear Regression", 
        forecast_days: int = 7
    ) -> Dict[str, Any]:
        """
        Generate forecast for a specific product.
        Returns metrics, historical series, and forecasted demand series for plotting.
        """
        # Fetch product metadata
        prod_sql = """
            SELECT p.product_id, p.product_name, p.current_stock, p.reorder_level,
                   p.safety_stock, s.lead_time, s.supplier_name
            FROM products p
            JOIN suppliers s ON p.supplier_id = s.supplier_id
            WHERE p.product_id = %s
        """
        prod_info = execute_read(prod_sql, (product_id,))
        if not prod_info:
            raise ValueError(f"Product {product_id} not found.")
        prod = prod_info[0]

        df_sales = cls.get_product_daily_sales(product_id)
        
        current_stock = prod['current_stock']
        lead_time = prod['lead_time']
        safety_stock = prod['safety_stock']
        reorder_level = prod['reorder_level']

        if df_sales.empty or len(df_sales) < 3:
            # Insufficient sales history fallback
            pred_daily = 0.0
            avg_daily = 0.0
            forecast_dates = [date.today() + timedelta(days=i) for i in range(1, forecast_days + 1)]
            forecast_values = [0.0] * forecast_days
        else:
            avg_daily = float(df_sales['quantity'].mean())
            
            if method == "Moving Average":
                # Window = 7 days or total length
                window = min(7, len(df_sales))
                pred_daily = float(df_sales['quantity'].rolling(window=window).mean().iloc[-1])
                pred_daily = max(0.0, pred_daily)
                forecast_dates = [df_sales['date'].max().date() + timedelta(days=i) for i in range(1, forecast_days + 1)]
                forecast_values = [round(pred_daily, 2)] * forecast_days
            else:
                # Scikit-learn Linear Regression
                df_sales['day_index'] = (df_sales['date'] - df_sales['date'].min()).dt.days
                X = df_sales[['day_index']].values
                y = df_sales['quantity'].values
                
                model = LinearRegression()
                model.fit(X, y)
                
                last_day = df_sales['day_index'].max()
                future_indices = np.array([[last_day + i] for i in range(1, forecast_days + 1)])
                preds = model.predict(future_indices)
                preds = np.clip(preds, 0, None) # No negative demand
                
                pred_daily = float(np.mean(preds))
                forecast_dates = [df_sales['date'].max().date() + timedelta(days=i) for i in range(1, forecast_days + 1)]
                forecast_values = [round(float(p), 2) for p in preds]

        pred_daily_rounded = round(pred_daily, 2)
        expected_demand = round(pred_daily * forecast_days, 1)

        # Stock-out calculation
        if pred_daily > 0.001:
            days_left = round(current_stock / pred_daily, 1)
        else:
            days_left = 999.0 # Practically infinite / No significant demand

        # Reorder Recommendation
        # Required Stock = (Predicted Daily Demand * Lead Time) + Safety Stock
        required_stock = (pred_daily * lead_time) + safety_stock
        recommended_qty = max(0, int(np.ceil(required_stock - current_stock)))
        
        if current_stock == 0:
            risk = "Out of Stock"
            recommendation = "Immediate Reorder Required"
            priority = "Critical"
        elif days_left <= lead_time or current_stock <= reorder_level:
            risk = "High Risk"
            recommendation = "Reorder Recommended"
            priority = "High"
        elif days_left <= (lead_time * 2):
            risk = "Moderate Risk"
            recommendation = "Monitor Closely"
            priority = "Medium"
        else:
            risk = "Healthy"
            recommendation = "No Reorder Required"
            priority = "Low"

        # Record forecast in DB for persistence and reporting
        try:
            execute_write(
                "INSERT INTO forecasts (product_id, forecast_date, predicted_demand, model_used) VALUES (%s, %s, %s, %s)",
                (product_id, date.today(), pred_daily_rounded, method)
            )
        except Exception:
            pass # Ignore duplicate or forecast insert hiccups

        return {
            "product_id": product_id,
            "product_name": prod['product_name'],
            "supplier_name": prod['supplier_name'],
            "current_stock": current_stock,
            "reorder_level": reorder_level,
            "safety_stock": safety_stock,
            "lead_time": lead_time,
            "avg_daily_demand": round(avg_daily, 2),
            "predicted_daily_demand": pred_daily_rounded,
            "forecast_period": forecast_days,
            "expected_demand": expected_demand,
            "days_left": days_left if days_left < 999 else "No significant demand detected",
            "days_left_numeric": days_left,
            "required_stock": round(required_stock, 1),
            "recommended_qty": recommended_qty,
            "recommendation": recommendation,
            "risk": risk,
            "priority": priority,
            "hist_dates": df_sales['date'].dt.strftime('%m-%d').tolist()[-30:] if not df_sales.empty else [],
            "hist_values": df_sales['quantity'].tolist()[-30:] if not df_sales.empty else [],
            "forecast_dates": [d.strftime('%m-%d') for d in forecast_dates],
            "forecast_values": forecast_values,
        }

    @classmethod
    def generate_all_forecasts(cls, method: str = "Linear Regression", forecast_days: int = 7) -> List[Dict[str, Any]]:
        """Calculate forecast for all products in system."""
        products = execute_read("SELECT product_id FROM products ORDER BY product_id ASC")
        results = []
        for p in products:
            res = cls.predict_product_demand(p['product_id'], method=method, forecast_days=forecast_days)
            results.append(res)
        return results

    @classmethod
    def get_reorder_recommendations(cls, method: str = "Linear Regression") -> List[Dict[str, Any]]:
        """Filter only products that require reorder or are critical."""
        all_fc = cls.generate_all_forecasts(method=method, forecast_days=7)
        # Filter where recommendation != 'No Reorder Required' or current_stock <= reorder_level
        reorders = [
            f for f in all_fc 
            if f['recommended_qty'] > 0 or f['current_stock'] <= f['reorder_level']
        ]
        # Sort by priority: Critical -> High -> Medium
        prio_map = {"Critical": 0, "High": 1, "Moderate Risk": 2, "Medium": 2, "Low": 3}
        reorders.sort(key=lambda x: (prio_map.get(x['risk'], 3), x['days_left_numeric']))
        return reorders

    @classmethod
    def get_forecasted_risk_count(cls) -> int:
        """Count products predicted to require replenishment for the dashboard."""
        try:
            reorders = cls.get_reorder_recommendations()
            return len(reorders)
        except Exception:
            return 0
