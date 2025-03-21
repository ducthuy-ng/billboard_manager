import sqlite3

def list_tables(db_path):
    """Lists all tables in the SQLite database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tables

def select_table(db_path, table_name):
    """Fetches all records from the given table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT * FROM {table_name}")
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        return columns, rows
    except sqlite3.Error as e:
        conn.close()
        return None, f"Error: {e}"

def main():
    db_path = "digital_signage.db"
    tables = list_tables(db_path)
    if not tables:
        print("No tables found in the database.")
        return
    
    print("Available tables:")
    for i, table in enumerate(tables, 1):
        print(f"{i}. {table}")
    
    choice = input("Enter the number of the table you want to view: ")
    try:
        table_name = tables[int(choice) - 1]
    except (IndexError, ValueError):
        print("Invalid choice.")
        return
    
    columns, rows = select_table(db_path, table_name)
    if isinstance(rows, str):
        print(rows)  # Print error message
        return
    
    print("\nTable Data:")
    print(" | ".join(columns))
    print("-" * 40)
    for row in rows:
        print(" | ".join(map(str, row)))

if __name__ == "__main__":
    main()
