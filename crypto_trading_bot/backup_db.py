import shutil
from datetime import datetime

backup_name = f'data/trades_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
shutil.copy2('data/trades.db', backup_name)
print(f'Backup created: {backup_name}')
