
import sys
import os
from sqlalchemy import text
from database import engine

def fix_schema():
    print("Fixing schema...")
    with engine.connect() as conn:
        try:
            # Check if column exists
            # For postgres:
            try:
                conn.execute(text("ALTER TABLE bot_configs ADD COLUMN reinvest_profits BOOLEAN DEFAULT TRUE;"))
                conn.commit()
                print("Added reinvest_profits column successfully.")
            except Exception as e:
                print(f"Column might already exist or error: {e}")
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    fix_schema()
