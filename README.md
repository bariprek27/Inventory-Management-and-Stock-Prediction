# StockWise - Desktop Inventory Management & Stock Forecasting System

StockWise is a desktop inventory management and predictive replenishment system designed for college course demonstration of advanced **Python programming**, **DBMS/SQL relational concepts**, **Data Analytics**, and **Machine Learning demand forecasting**.

---

## 🎨 Color Palette Implementation
StockWise strictly adheres to the requested 4-color design specification:
* **Dark Teal (`#001E23`)**: Sidebar background, primary window headers, section labels, borders, dark text accents.
* **Teal (`#007887`)**: Primary action buttons, active navigation, table column headers, card titles.
* **Aqua (`#78E6DC`)**: Accent elements, highlight buttons, data visualizations, statistics focus.
* **Cream (`#FAF6EE`)**: Off-white light surface color used as the exclusive background across all views.

---

## 🛠 Technology Stack
* **GUI / Presentation**: Tkinter & ttk (Single-window central content switching, modern ttk clam styles)
* **Application / Logic**: Python 3.10+
* **Database**: MySQL 8.x using `mysql-connector-python` with connection pooling
* **Authentication**: `bcrypt` password hashing with salt (Admin & Staff roles)
* **Data Analytics**: `Pandas` and `NumPy` for trend grouping, sales aggregation, metrics calculation
* **Data Visualization**: Embedded `Matplotlib` Figures inside Tkinter canvas
* **Machine Learning & Forecasting**: `Scikit-learn` Linear Regression & Moving Average models

---

## 🗄️ Database Architecture (`stockwise`)
The system demonstrates normalized 3NF database architecture:

1. `users`: Stores user credentials (`password_hash`), names, and authorization roles (`admin`, `staff`).
2. `categories`: Normalized item classification.
3. `suppliers`: Vendor metadata including supplier lead times (in days).
4. `products`: Catalog tracking `purchase_price`, `selling_price`, `current_stock`, `reorder_level`, and `safety_stock`.
5. `purchases` & `purchase_items`: Inbound stock purchase orders with ACID transaction recording.
6. `sales` & `sale_items`: POS checkout outflow transactions with ACID consistency.
7. `inventory_transactions`: Complete immutable audit trail for all stock movements (`PURCHASE`, `SALE`, `ADJUSTMENT`).
8. `forecasts`: Historical repository of predictive demand outputs and algorithm types.
9. **SQL Views**:
   * `v_inventory_overview`: Joins products, categories, suppliers and calculates stock status dynamically (`Healthy`, `Low Stock`, `Out of Stock`, `Overstock`).
   * `v_daily_sales`: Daily aggregated revenue, units, and order count.
   * `v_product_sales_summary`: Product-level sales volume and total revenue performance.

---

## 📁 Project Directory Structure
```
StockWise/
│
├── main.py                     # Application entrypoint & view coordinator
├── requirements.txt            # Python dependencies
├── README.md                   # System documentation
│
├── database/
│   ├── connection.py           # MySQL connection pool manager
│   ├── schema.sql              # Normalized MySQL DDL & SQL views
│   ├── queries.py              # Centralized SQL transactions & queries
│   └── seed_data.py            # Populates 30+ products, 8 suppliers, 280+ sales
│
├── gui/
│   ├── theme.py                # Color tokens & TTK style configuration
│   ├── widgets.py              # StatCard, TableView, SearchBar reusable components
│   ├── login.py                # Authentication screen
│   ├── dashboard.py            # Overview dashboard with 8 dynamic cards & quick actions
│   ├── products.py             # Product catalog CRUD & filters
│   ├── categories.py           # Category management & product inspection
│   ├── suppliers.py            # Supplier CRUD, supplied catalog & PO history
│   ├── purchases.py            # Purchase order generation & stock inflow
│   ├── sales.py                # Sales POS terminal & stock outflow
│   ├── inventory.py            # Live inventory tracking, filters, audit trail & adjustments
│   ├── analytics.py            # Sales analysis, date filter, KPIs & Matplotlib charts
│   ├── forecasting.py          # Scikit-learn Linear Regression & Moving Average ML
│   ├── reorder.py              # Replenishment recommendations & priority sorting
│   └── reports.py              # Multi-module reports generator with CSV export
│
├── services/
│   ├── inventory_service.py    # Inventory & stock adjustment logic
│   ├── sales_service.py        # Sales transaction coordinator
│   ├── purchase_service.py     # PO transaction coordinator
│   ├── analytics_service.py    # Pandas & NumPy analysis calculations
│   ├── forecasting_service.py  # Demand forecasting & stock-out predictions
│   └── reorder_service.py      # Restock requirement computations
│
└── utils/
    ├── security.py             # Bcrypt hashing & CurrentUser session tracker
    ├── validators.py           # Input sanitization and validators
    └── csv_export.py           # Pandas CSV file export utilities
```

---

## 🚀 Setup & Execution Instructions

### 1. Configure MySQL Credentials
StockWise reads MySQL connection settings from environment variables or defaults to `localhost:3306`, user `root`, password `""`.
You can configure them via shell or PowerShell before running:
```powershell
$env:SW_DB_HOST="localhost"
$env:SW_DB_PORT="3306"
$env:SW_DB_USER="root"
$env:SW_DB_PASS="your_mysql_password"
$env:SW_DB_NAME="stockwise"
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Initialize Database & Seed Sample Data
Execute the seed script to automatically create the tables and inject realistic demonstration records (32 products, 8 suppliers, 60 purchase orders, and 280 sales spanning 90 days):
```bash
python database/seed_data.py
```

### 4. Launch StockWise Desktop
```bash
python main.py
```

### Default Login Accounts:
* **Administrator**:
  * Username: `admin`
  * Password: `admin123`
* **Staff Member**:
  * Username: `staff`
  * Password: `staff123`

---

## 🔮 Predictive Demand & Reorder Formulas

### 1. Estimated Days Until Stock-Out
$$\text{Days Until Stock-Out} = \frac{\text{Current Stock}}{\text{Predicted Daily Demand}}$$

### 2. Required Stock Level
$$\text{Required Stock} = (\text{Predicted Daily Demand} \times \text{Supplier Lead Time}) + \text{Safety Stock}$$

### 3. Recommended Order Quantity
$$\text{Recommended Order Quantity} = \max(0, \lceil \text{Required Stock} - \text{Current Stock} \rceil)$$
