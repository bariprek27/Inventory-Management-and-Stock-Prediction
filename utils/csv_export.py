"""
utils/csv_export.py
Utilities to export query results or dataframes to CSV.
"""
from tkinter import filedialog, messagebox
import pandas as pd
from typing import List, Dict, Any, Optional

def export_dataframe_to_csv(df: pd.DataFrame, default_filename: str = "export.csv", title: str = "Export Data") -> Optional[str]:
    """Prompt user for a destination file and save DataFrame as CSV."""
    if df.empty:
        messagebox.showwarning("Export Warning", "No data available to export.")
        return None
        
    filepath = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        initialfile=default_filename,
        title=title
    )
    if filepath:
        try:
            df.to_csv(filepath, index=False)
            messagebox.showinfo("Export Successful", f"Data exported successfully to:\n{filepath}")
            return filepath
        except Exception as e:
            messagebox.showerror("Export Failed", f"Failed to save CSV file:\n{str(e)}")
            return None
    return None

def export_records_to_csv(records: List[Dict[str, Any]], default_filename: str = "export.csv", title: str = "Export Data") -> Optional[str]:
    """Helper to export a list of dict records directly."""
    if not records:
        messagebox.showwarning("Export Warning", "No records found to export.")
        return None
    df = pd.DataFrame(records)
    return export_dataframe_to_csv(df, default_filename=default_filename, title=title)
