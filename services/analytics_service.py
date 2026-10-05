"""
services/analytics_service.py
Performs sales analysis using Pandas, NumPy, and SQL:
- Daily, Weekly, Monthly sales
- Revenue & Quantity sold
- Best-selling & Slow-moving products
- Category-wise sales
- Sales growth and daily averages
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from database.queries import execute_read

class AnalyticsService:
    @staticmethod
    def get_sales_analytics(start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Pull raw sales and sale_items data between start_date and end_date,
        convert into Pandas DataFrame and compute comprehensive analytics.
        """
        sql = """
            SELECT 
                s.sale_id,
                s.sale_date,
                si.product_id,
                p.product_name,
                c.category_name,
                si.quantity,
                si.unit_price,
                (si.quantity * si.unit_price) AS line_total
            FROM sales s
            JOIN sale_items si ON s.sale_id = si.sale_id
            JOIN products p ON si.product_id = p.product_id
            JOIN categories c ON p.category_id = c.category_id
            WHERE 1=1
        """
        params = []
        if start_date:
            sql += " AND s.sale_date >= %s"
            params.append(start_date)
        if end_date:
            sql += " AND s.sale_date <= %s"
            params.append(end_date)
            
        sql += " ORDER BY s.sale_date ASC"
        
        rows = execute_read(sql, tuple(params))
        if not rows:
            return {
                "has_data": False,
                "total_revenue": 0.0,
                "total_units": 0,
                "total_orders": 0,
                "avg_daily_sales": 0.0,
                "daily_trend": pd.DataFrame(),
                "top_products": pd.DataFrame(),
                "category_sales": pd.DataFrame(),
                "fast_moving": pd.DataFrame(),
                "slow_moving": pd.DataFrame(),
            }

        df = pd.DataFrame(rows)
        df['sale_date'] = pd.to_datetime(df['sale_date'])
        df['quantity'] = pd.to_numeric(df['quantity'])
        df['line_total'] = pd.to_numeric(df['line_total'])

        total_revenue = float(df['line_total'].sum())
        total_units = int(df['quantity'].sum())
        total_orders = int(df['sale_id'].nunique())

        # Daily trend
        daily_trend = df.groupby(df['sale_date'].dt.date).agg(
            revenue=('line_total', 'sum'),
            units=('quantity', 'sum'),
            orders=('sale_id', 'nunique')
        ).reset_index().rename(columns={'sale_date': 'date'})

        days_count = max(1, len(daily_trend))
        avg_daily_sales = float(total_revenue / days_count)

        # Top 5 products by quantity
        top_products = df.groupby(['product_id', 'product_name']).agg(
            total_sold=('quantity', 'sum'),
            revenue=('line_total', 'sum')
        ).reset_index().sort_values(by='total_sold', ascending=False).head(5)

        # Category-wise sales
        category_sales = df.groupby('category_name').agg(
            revenue=('line_total', 'sum'),
            units=('quantity', 'sum')
        ).reset_index().sort_values(by='revenue', ascending=False)

        # Fast moving vs Slow moving
        product_performance = df.groupby(['product_id', 'product_name', 'category_name']).agg(
            units_sold=('quantity', 'sum'),
            revenue=('line_total', 'sum')
        ).reset_index()

        fast_moving = product_performance.sort_values(by='units_sold', ascending=False).head(5)
        slow_moving = product_performance.sort_values(by='units_sold', ascending=True).head(5)

        return {
            "has_data": True,
            "total_revenue": total_revenue,
            "total_units": total_units,
            "total_orders": total_orders,
            "avg_daily_sales": avg_daily_sales,
            "daily_trend": daily_trend,
            "top_products": top_products,
            "category_sales": category_sales,
            "fast_moving": fast_moving,
            "slow_moving": slow_moving,
            "raw_df": df
        }
