import MySQLdb
import sys

def drop_tables():
    try:
        db = MySQLdb.connect(
            host="127.0.0.1",
            user="root",
            passwd="3236",
            port=3306,
            db="dbms"
        )
        cursor = db.cursor()
        # Drop tables in reverse order of dependencies
        tables = [
            "doctor_analysisresult", 
            "doctor_assessmentmedia", 
            "doctor_assessment", 
            "doctor_doctorprofile",
            "django_migrations" # Drop migrations too to start fresh on this DB
        ]
        
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        for table in tables:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
            print(f"Dropped {table}")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        
        db.commit()
        db.close()
        print("Required tables dropped successfully.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    drop_tables()
