import os
import sqlite3
import pandas as pd
import logging

# Configure professional logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def generate_soil_database(archive_folder="archive", csv_filename="soil.csv", db_folder="Databases", db_name="district_soil.db"):
    """
    Reads soil.csv from the archive folder, cleans column names, 
    and saves it into a structured SQLite database inside the Databases folder.
    """
    # 1. Ensure target 'Databases' directory exists
    os.makedirs(db_folder, exist_ok=True)
    db_path = os.path.join(db_folder, db_name)
    target_csv_path = os.path.join(archive_folder, csv_filename)

    # 2. Verify source file existence
    if not os.path.exists(target_csv_path):
        logging.error(f"Could not find '{csv_filename}' inside '{archive_folder}/'. Check your file path.")
        return

    # 3. Load CSV data via pandas
    logging.info(f"Loading '{csv_filename}' from '{archive_folder}/'...")
    df = pd.read_csv(target_csv_path)

    # 4. Clean column headers: Strip whitespace, lowercase, handle percentages and spaces
    # Example: 'District ' -> 'district', 'Zn %' -> 'zn_pct', 'Fe%' -> 'fe_pct'
    cleaned_columns = []
    for col in df.columns:
        c_clean = col.strip().lower().replace(' %', '_pct').replace('%', '_pct').replace(' ', '_')
        cleaned_columns.append(c_clean)
    
    df.columns = cleaned_columns
    logging.info(f"Successfully mapped columns: {df.columns.tolist()}")

    # 5. Connect to SQLite and write database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Drop table if it exists to allow clean regeneration
    cursor.execute('DROP TABLE IF EXISTS district_soil')

    # Dynamically create table schema based on cleaned column headers
    cursor.execute('''
        CREATE TABLE district_soil (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            district TEXT,
            zn_pct REAL,
            fe_pct REAL,
            cu_pct REAL,
            mn_pct REAL,
            b_pct REAL,
            s_pct REAL
        )
    ''')

    # 6. Insert rows securely with error handling for missing values
    inserted_count = 0
    for _, row in df.iterrows():
        district_val = str(row.get('district', '')).strip()
        
        cursor.execute('''
            INSERT INTO district_soil (district, zn_pct, fe_pct, cu_pct, mn_pct, b_pct, s_pct)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            district_val if district_val and district_val != 'nan' else "Unknown",
            float(row.get('zn_pct', 0.0)),
            float(row.get('fe_pct', 0.0)),
            float(row.get('cu_pct', 0.0)),
            float(row.get('mn_pct', 0.0)),
            float(row.get('b_pct', 0.0)),
            float(row.get('s_pct', 0.0))
        ))
        inserted_count += 1

    conn.commit()
    conn.close()
    
    logging.info(f"Successfully generated database at: {db_path}")
    logging.info(f"Total district records imported: {inserted_count}")

if __name__ == "__main__":
    generate_soil_database()