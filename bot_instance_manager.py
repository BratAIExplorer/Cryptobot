"""
CryptoBots V3 - Bot Instance Manager
Manages multiple bot instances across different strategies and trading pairs.
"""

import uuid
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from strategies import BuyDipStrategy, TakeProfitStrategy, TrendFollowingStrategy


class BotInstance:
    """
    Represents a single bot instance with its own configuration,
    strategy, trading pair, and balance allocation.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize a bot instance.
        
        Args:
            config: Bot configuration dictionary
        """
        self.id = config.get('id', str(uuid.uuid4()))
        self.name = config.get('name', f"Bot-{self.id[:8]}")
        self.strategy_type = config.get('strategy', 'buy_dip')
        self.symbol = config.get('symbol', 'BTC/USDT')
        self.max_allocation = config.get('max_allocation', 100.0)
        self.enabled = config.get('enabled', True)
        
        # Parse created_at if it's a string
        created_at = config.get('created_at', datetime.now())
        if isinstance(created_at, str):
            try:
                self.created_at = datetime.fromisoformat(created_at)
            except ValueError:
                self.created_at = datetime.now()
        else:
            self.created_at = created_at
        
        # Initialize strategy
        self.strategy = self._create_strategy(config.get('strategy_config', {}))
        
        # Performance tracking
        self.total_pnl = config.get('total_pnl', 0.0)
        self.total_trades = config.get('total_trades', 0)
        self.winning_trades = config.get('winning_trades', 0)
        self.positions = config.get('positions', [])
        self.balance_used = config.get('balance_used', 0.0)
        
        # Status
        self.status = config.get('status', 'idle')
        self.last_activity = None
        self.error_message = None
    
    def _create_strategy(self, strategy_config: Dict):
        """Create strategy instance based on type."""
        strategy_map = {
            'buy_dip': BuyDipStrategy,
            'take_profit': TakeProfitStrategy,
            'trend_following': TrendFollowingStrategy
        }
        
        strategy_class = strategy_map.get(self.strategy_type)
        if strategy_class:
            return strategy_class(strategy_config)
        return None
    
    def get_available_balance(self) -> float:
        """Get available balance for this bot."""
        return self.max_allocation - self.balance_used
    
    def can_trade(self, amount: float) -> bool:
        """Check if bot can trade given amount."""
        return self.enabled and self.get_available_balance() >= amount
    
    def update_performance(self, trade: Dict):
        """Update bot performance with new trade."""
        pnl = trade.get('pnl', 0)
        self.total_pnl += pnl
        self.total_trades += 1
        
        if pnl > 0:
            self.winning_trades += 1
        
        self.last_activity = datetime.now()
    
    def get_win_rate(self) -> float:
        """Calculate win rate percentage."""
        if self.total_trades == 0:
            return 0.0
        return (self.winning_trades / self.total_trades) * 100
    
    def get_status_emoji(self) -> str:
        """Get emoji representing bot status."""
        status_map = {
            'idle': '⚪',
            'running': '🟢',
            'paused': '🟡',
            'error': '🔴'
        }
        return status_map.get(self.status, '⚪')
    
    def to_dict(self) -> Dict:
        """Convert bot instance to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'strategy': self.strategy_type,
            'symbol': self.symbol,
            'max_allocation': self.max_allocation,
            'balance_used': self.balance_used,
            'balance_available': self.get_available_balance(),
            'enabled': self.enabled,
            'status': self.status,
            'total_pnl': self.total_pnl,
            'total_trades': self.total_trades,
            'win_rate': self.get_win_rate(),
            'positions': len(self.positions),
            'created_at': self.created_at.isoformat(),
            'winning_trades': self.winning_trades
        }


class BotInstanceManager:
    """
    Manages multiple bot instances with JSON persistence.
    """
    
    CONFIG_FILE = Path("config/bots.json")
    
    def __init__(self):
        """Initialize bot instance manager."""
        self.bots: Dict[str, BotInstance] = {}
        self._load_bots()
    
    def _ensure_config_dir(self):
        """Ensure config directory exists."""
        self.CONFIG_FILE.parent.mkdir(exist_ok=True)
    
    def _load_bots(self):
        """Load bots from JSON file."""
        if not self.CONFIG_FILE.exists():
            return
            
        try:
            with open(self.CONFIG_FILE, 'r') as f:
                data = json.load(f)
                for bot_config in data:
                    bot = BotInstance(bot_config)
                    self.bots[bot.id] = bot
        except Exception as e:
            print(f"❌ Failed to load bots: {e}")
    
    def _save_bots(self):
        """Save bots to JSON file."""
        self._ensure_config_dir()
        try:
            data = [bot.to_dict() for bot in self.bots.values()]
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"❌ Failed to save bots: {e}")
    
    def create_bot(self, config: Dict) -> BotInstance:
        """
        Create a new bot instance.
        
        Args:
            config: Bot configuration
            
        Returns:
            Created bot instance
        """
        bot = BotInstance(config)
        self.bots[bot.id] = bot
        self._save_bots()
        return bot
    
    def get_bot(self, bot_id: str) -> Optional[BotInstance]:
        """Get bot by ID."""
        return self.bots.get(bot_id)
    
    def get_all_bots(self) -> List[BotInstance]:
        """Get all bot instances."""
        return list(self.bots.values())
    
    def get_active_bots(self) -> List[BotInstance]:
        """Get all active (enabled) bots."""
        return [bot for bot in self.bots.values() if bot.enabled]
    
    def get_running_bots(self) -> List[BotInstance]:
        """Get all running bots."""
        return [bot for bot in self.bots.values() if bot.status == 'running']
    
    def get_bots_by_strategy(self, strategy_type: str) -> List[BotInstance]:
        """Get all bots using a specific strategy."""
        return [bot for bot in self.bots.values() if bot.strategy_type == strategy_type]
    
    def get_bots_by_symbol(self, symbol: str) -> List[BotInstance]:
        """Get all bots trading a specific symbol."""
        return [bot for bot in self.bots.values() if bot.symbol == symbol]
    
    def remove_bot(self, bot_id: str) -> bool:
        """Remove a bot instance."""
        if bot_id in self.bots:
            del self.bots[bot_id]
            self._save_bots()
            return True
        return False
    
    def start_bot(self, bot_id: str):
        """Start a bot."""
        bot = self.get_bot(bot_id)
        if bot:
            bot.status = 'running'
            bot.enabled = True
            self._save_bots()
    
    def pause_bot(self, bot_id: str):
        """Pause a bot."""
        bot = self.get_bot(bot_id)
        if bot:
            bot.status = 'paused'
            self._save_bots()
    
    def stop_bot(self, bot_id: str):
        """Stop a bot."""
        bot = self.get_bot(bot_id)
        if bot:
            bot.status = 'idle'
            bot.enabled = False
            self._save_bots()
    
    def get_total_pnl(self) -> float:
        """Get total P&L across all bots."""
        return sum(bot.total_pnl for bot in self.bots.values())
    
    def get_total_trades(self) -> int:
        """Get total trades across all bots."""
        return sum(bot.total_trades for bot in self.bots.values())
    
    def get_overall_win_rate(self) -> float:
        """Get overall win rate across all bots."""
        total_trades = self.get_total_trades()
        if total_trades == 0:
            return 0.0
        
        total_wins = sum(bot.winning_trades for bot in self.bots.values())
        return (total_wins / total_trades) * 100
    
    def to_dict(self) -> Dict:
        """Get summary dictionary."""
        return {
            'total_bots': len(self.bots),
            'active_bots': len(self.get_active_bots()),
            'running_bots': len(self.get_running_bots()),
            'total_pnl': self.get_total_pnl(),
            'total_trades': self.get_total_trades(),
            'overall_win_rate': self.get_overall_win_rate(),
            'bots': [bot.to_dict() for bot in self.bots.values()]
        }
