
import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import sqlite3

# Add current dir to path to import models
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import BotConfig, User
from database import SessionLocal, engine

load_dotenv()

# 1. Get running bots from SQLite
BOT_DB_PATH = os.getenv("BOT_DB_PATH", "../../data/multi/trades_paper.db")
if not os.path.isabs(BOT_DB_PATH):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # Adjust for being in enterprise/backend
    BOT_DB_PATH = os.path.abspath(os.path.join(base_dir, "../../data/multi/trades_paper.db"))

print(f"Reading bot DB from: {BOT_DB_PATH}")
conn = sqlite3.connect(f"file:{BOT_DB_PATH}?mode=ro", uri=True)
cursor = conn.cursor()
cursor.execute("SELECT strategy FROM bot_status WHERE status='RUNNING'")
running_bots = [row[0] for row in cursor.fetchall()]
conn.close()

print(f"Found {len(running_bots)} running bots: {running_bots}")

# 2. Get existing configs from Enterprise DB
db = SessionLocal()
try:
    # Get admin user
    admin = db.query(User).filter(User.email == "admin@cryptobot.com").first()
    if not admin:
        print("Admin user not found!")
        sys.exit(1)
        
    existing_configs = db.query(BotConfig).filter(BotConfig.user_id == admin.id).all()
    existing_names = [config.bot_name for config in existing_configs]
    print(f"Found {len(existing_configs)} existing configs: {existing_names}")

    # 3. Create missing configs
    for bot_name in running_bots:
        if bot_name not in existing_names:
            print(f"Creating config for missing bot: {bot_name}")
            
            # Determine type
            bot_type = "Grid Trading" if "Grid" in bot_name else "Opportunistic"
            
            new_config = BotConfig(
                user_id=admin.id,
                bot_name=bot_name,
                bot_type=bot_type,
                config={"budget": 300, "enabled": True},
                is_active=True,
                is_paper_mode=True,
                reinvest_profits=True
            )
            db.add(new_config)
            
    db.commit()
    print("Sync complete!")
    
except Exception as e:
    print(f"Error: {e}")
    db.rollback()
finally:
    db.close()
