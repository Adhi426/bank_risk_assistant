import sqlite3
from datetime import datetime, timedelta

def init_db(db_path: str = "transactions.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id TEXT PRIMARY KEY,
            name TEXT,
            account_type TEXT,
            profile_summary TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            txn_id TEXT PRIMARY KEY,
            customer_id TEXT,
            timestamp TEXT,
            amount REAL,
            payee TEXT,
            channel TEXT,
            description TEXT,
            FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
        )
    """)

    # Reset sample data
    existing_customer = conn.execute(
        "SELECT COUNT(*) AS count FROM customers"
    ).fetchone()[0]

    if existing_customer > 0:
        conn.commit()
        conn.close()
        return

    # 1. CUST_001: Clean Profile (Pure everyday groceries, utility, salary)
    cursor.execute("INSERT INTO customers VALUES (?, ?, ?, ?)", 
                   ("CUST_001", "Priya Sharma", "Savings", "Salaried professional, standard monthly utility & grocery spend."))
    base_time = datetime(2026, 8, 1, 10, 0)
    clean_txns = [
        ("TXN_101", "CUST_001", (base_time + timedelta(days=1)).isoformat(), 1500.0, "FreshMart Supermarket", "POS", "Weekly Groceries"),
        ("TXN_102", "CUST_001", (base_time + timedelta(days=3)).isoformat(), 450.0, "Metro Coffee Co", "UPI", "Coffee and Snacks"),
        ("TXN_103", "CUST_001", (base_time + timedelta(days=5)).isoformat(), 2800.0, "Airtel Broadband", "NetBanking", "Internet Bill"),
        ("TXN_104", "CUST_001", (base_time + timedelta(days=10)).isoformat(), 3200.0, "Apollo Pharmacy", "UPI", "Medicine Refill"),
        ("TXN_105", "CUST_001", (base_time + timedelta(days=15)).isoformat(), 1800.0, "FreshMart Supermarket", "POS", "Groceries"),
        ("TXN_106", "CUST_001", (base_time + timedelta(days=20)).isoformat(), 750.0, "BookStore", "UPI", "Books"),
    ]
    cursor.executemany("INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?)", clean_txns)

    # 2. CUST_002: Velocity Spike / New Payee at Odd Hours (Account Takeover style)
    cursor.execute("INSERT INTO customers VALUES (?, ?, ?, ?)", 
                   ("CUST_002", "Vikram Rathore", "Current", "Small business owner, regular supplier payouts between 10 AM - 6 PM."))
    odd_hour = datetime(2026, 8, 15, 3, 14) # 3:14 AM
    burst_txns = [
        # Baseline normal
        ("TXN_201", "CUST_002", "2026-08-01T11:00:00", 12000.0, "Steel Supplies Ltd", "NEFT", "Raw material invoice"),
        ("TXN_202", "CUST_002", "2026-08-05T14:30:00", 8500.0, "Packaging Co", "IMPS", "Carton supply"),
        # Anomalies: Late night bursts to brand-new payee
        ("TXN_203", "CUST_002", odd_hour.isoformat(), 95000.0, "Unknown Payee - Alpha Holdings", "IMPS", "Immediate Transfer"),
        ("TXN_204", "CUST_002", (odd_hour + timedelta(minutes=12)).isoformat(), 98000.0, "Unknown Payee - Alpha Holdings", "IMPS", "Urgent Clearance"),
        ("TXN_205", "CUST_002", (odd_hour + timedelta(minutes=25)).isoformat(), 92000.0, "Unknown Payee - Alpha Holdings", "IMPS", "Consulting Fee"),
    ]
    cursor.executemany("INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?)", burst_txns)

    # 3. CUST_003: Structuring / Smurfing (Repeated amounts right below reporting limit)
    cursor.execute("INSERT INTO customers VALUES (?, ?, ?, ?)", 
                   ("CUST_003", "Ananya Sen", "Savings", "Freelance consultant, typical monthly inflow of 50k-80k."))
    struct_time = datetime(2026, 8, 20, 16, 0)
    struct_txns = [
        ("TXN_301", "CUST_003", "2026-08-02T12:00:00", 3500.0, "Co-Working Space", "UPI", "Desk Rent"),
        ("TXN_302", "CUST_003", (struct_time).isoformat(), 49900.0, "Apex Crypto Traders", "IMPS", "Services"),
        ("TXN_303", "CUST_003", (struct_time + timedelta(hours=2)).isoformat(), 49500.0, "Apex Crypto Traders", "IMPS", "Settlement"),
        ("TXN_304", "CUST_003", (struct_time + timedelta(hours=4)).isoformat(), 49800.0, "Apex Crypto Traders", "IMPS", "Consulting"),
    ]
    cursor.executemany("INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?)", struct_txns)

    # 4. CUST_004: High Net Worth Clean Baseline (High values, zero anomalies)
    cursor.execute("INSERT INTO customers VALUES (?, ?, ?, ?)", 
                   ("CUST_004", "Arjun Mehta", "HNI Wealth Savings", "Corporate executive, regular high-value transfers for wealth management and premium living."))
    hnw_txns = [
        ("TXN_401", "CUST_004", "2026-08-01T11:00:00", 150000.0, "HDFC Mutual Funds", "NetBanking", "SIP Investment"),
        ("TXN_402", "CUST_004", "2026-08-05T15:30:00", 120000.0, "Prestige Luxury Living", "NEFT", "Apartment Maintenance"),
        ("TXN_403", "CUST_004", "2026-08-12T10:15:00", 85000.0, "Emirates Airlines", "Credit Card", "Business Travel"),
        ("TXN_404", "CUST_004", "2026-08-18T14:00:00", 140000.0, "HDFC Mutual Funds", "NetBanking", "Portfolio Topup"),
    ]
    cursor.executemany("INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?)", hnw_txns)

    conn.commit()
    conn.close()

    # Seed initial history if empty
    from src.history import seed_initial_history
    seed_initial_history(db_path)

if __name__ == "__main__":
    init_db()