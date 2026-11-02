import sqlite3
from pathlib import Path

DATABASE_DIR = Path(__file__).resolve().parent / "Databases"

def inspect_database(db_path=DATABASE_DIR / "agricultural_knowledge.db"):
    print(f"--- Inspecting {db_path} ---")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"Tables found: {tables}\n")
    
    for table in tables:
        table_name = table[0]
        print(f"--- Contents of table: {table_name} ---")
        
        # Fetch rows
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 10") # Showing first 10 rows
        rows = cursor.fetchall()
        
        # Get column names
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in cursor.fetchall()]
        print(" | ".join(columns))
        print("-" * 50)
        
        for row in rows:
            print(row)
        print("\n")
        
    conn.close()

if __name__ == "__main__":
    inspect_database(DATABASE_DIR / "agricultural_knowledge.db")
    inspect_database(DATABASE_DIR / "farm_telemetry.db")