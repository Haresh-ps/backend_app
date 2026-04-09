import MySQLdb
import sys

def clear_db():
    try:
        db = MySQLdb.connect(
            host="127.0.0.1",
            user="root",
            passwd="3236",
            port=3306,
            db="dbms"
        )
        cursor = db.cursor()
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        
        # Get all table names
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        for (table_name,) in tables:
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            print(f"Dropped table: {table_name}")
            
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        db.commit()
        db.close()
        print("Database 'dbms' cleared successfully.")
    except Exception as e:
        print(f"Error clearing database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    clear_db()
