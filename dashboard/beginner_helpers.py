"""
Beginner-Friendly Dashboard Helper Functions
Translates technical trading jargon into plain English that anyone can understand.

This module follows the "Grandma Rule" - if grandma can't understand it, we simplify it.
"""

from typing import Dict, Tuple, Optional
from enum import Enum


class TrafficLight(Enum):
    """Simple color-coded rating system"""
    EXCELLENT = ("🟢", "#00ff88", "Excellent")
    GOOD = ("🟡", "#90EE90", "Good")
    FAIR = ("🟠", "#ffaa00", "Fair")
    POOR = ("🔴", "#ff4444", "Poor")


# ==================== JARGON DICTIONARY ====================

JARGON_DICTIONARY = {
    "confluence_score": {
        "simple_name": "Safety Score",
        "short_explanation": "How safe is it to buy this coin right now?",
        "detailed_explanation": """
        Think of this like a report card for buying a coin.
        
        The bot checks 4 important things:
        • Is the price good? (Technical Analysis)
        • Are smart traders buying? (On-Chain Data)
        • Is the market healthy? (Market Mood)
        • Is the coin useful? (Fundamentals)
        
        Higher scores mean safer buys!
        """,
        "ranges": {
            (85, 100): ("🟢 Excellent", "Great time to buy!", "The stars are aligned! This is a high-quality buying opportunity."),
            (70, 84): ("🟢 Good", "Good opportunity", "Solid buy signal. Most indicators look positive."),
            (50, 69): ("🟡 Decent", "Okay to buy", "Mixed signals. Could go either way."),
            (30, 49): ("🟠 Fair", "Wait for better", "Not the best time. Better opportunities likely coming."),
            (0, 29): ("🔴 Poor", "Don't buy now", "Too risky. Wait for conditions to improve.")
        }
    },
    
    "rsi": {
        "simple_name": "Momentum Meter",
        "short_explanation": "Is the price moving fast up or down?",
        "detailed_explanation": """
        RSI (Relative Strength Index) measures how fast the price is changing.
        
        Think of it like a car speedometer:
        • Below 30: "Oversold" - Price dropped fast, might bounce back up
        • 30-70: "Normal" - Price is moving at a steady pace
        • Above 70: "Overbought" - Price went up fast, might fall back down
        
        The bot looks for "oversold" coins to buy cheap!
        """,
        "ranges": {
            (0, 30): ("🟢", "Oversold - Good to buy", "Price dropped a lot. Good buying opportunity!"),
            (30, 50): ("🟡", "Neutral-Low", "Price is stable on the lower side."),
            (50, 70): ("🟡", "Neutral-High", "Price is stable on the higher side."),
            (70, 100): ("🔴", "Overbought - Don't buy", "Price went up too fast. Might drop soon.")
        }
    },
    
    "unrealized_pnl": {
        "simple_name": "Paper Profit/Loss",
        "short_explanation": "How much you'd gain or lose if you sold right now",
        "detailed_explanation": """
        This shows how much money you'd make or lose if you sold the coin at the current price.
        
        It's called "paper" profit/loss because you haven't actually sold yet.
        The money isn't real until you sell!
        
        • Green (+): You'd make money if you sold now
        • Red (-): You'd lose money if you sold now
        
        The bot will automatically sell when profit reaches your target.
        """
    },
    
    "market_regime": {
        "simple_name": "Market Mood",
        "short_explanation": "Is the whole crypto market happy or scared?",
        "detailed_explanation": """
        This tells you the overall "mood" of the cryptocurrency market.
        
        Think of it like the weather:
        • ☀️ Bull Market: Everyone is optimistic, prices going up
        • 🌤️ Neutral: Market is calm, could go either way
        • ⛈️ Bear Market: Everyone is pessimistic, prices falling
        • 🌪️ Crisis: Major crash happening, stay safe!
        
        The bot stops buying during crisis mode to protect your money.
        """,
        "ranges": {
            "BULL_CONFIRMED": ("🟢", "☀️ Sunny (Bull Market)", "Great time to trade! Market is strong."),
            "TRANSITION_BULLISH": ("🟢", "🌤️ Getting Sunny", "Market is improving. Cautiously optimistic."),
            "UNDEFINED": ("🟡", "🌥️ Cloudy (Neutral)", "Market is uncertain. Be careful."),
            "TRANSITION_BEARISH": ("🟠", "⛅ Getting Cloudy", "Market is weakening. Extra caution needed."),
            "BEAR_CONFIRMED": ("🔴", "⛈️ Stormy (Bear Market)", "Market is falling. Bot will be very selective."),
            "CRISIS": ("🔴", "🌪️ Hurricane (Crisis!)", "⚠️ Bot stopped trading to protect your money!")
        }
    },
    
    "stop_loss": {
        "simple_name": "Safety Net",
        "short_explanation": "Automatic sell if price drops too much",
        "detailed_explanation": """
        A stop loss is like a safety parachute for your investment.
        
        If the price drops too much (usually 5-10%), the bot automatically
        sells to prevent bigger losses.
        
        Example: You buy at $100 with 5% stop loss
        → Bot auto-sells if price drops to $95
        → You lose $5 instead of waiting and potentially losing $20+
        
        It's better to lose a little than lose a lot!
        """
    },
    
    "take_profit": {
        "simple_name": "Win Target",
        "short_explanation": "Automatic sell when you've made enough profit",
        "detailed_explanation": """
        Take profit is like scoring a goal in soccer - you lock in your win!
        
        When the price goes up by your target amount (usually 5-10%), 
        the bot automatically sells to secure your profit.
        
        Example: You buy at $100 with 5% take profit
        → Bot auto-sells at $105
        → You make $5 profit! 🎉
        
        Smart traders always have a win target instead of being greedy.
        """
    },
    
    "sma_trend": {
        "simple_name": "Direction Finder",
        "short_explanation": "Is the price going up or down overall?",
        "detailed_explanation": """
        SMA (Simple Moving Average) shows the overall direction of the price.
        
        Think of it like a compass for trading:
        • Price ABOVE the line = ⬆️ Uptrend (generally going up)
        • Price ON the line = ↔️ Sideways (staying flat)
        • Price BELOW the line = ⬇️ Downtrend (generally going down)
        
        The bot prefers to buy when the trend is going up!
        """
    },
    
    "exposure": {
        "simple_name": "How Much You Own",
        "short_explanation": "Total amount of money you have in this coin",
        "detailed_explanation": """
        Exposure means how much of your total money is in this particular coin.
        
        Example: You have $1,000 total
        → You own $200 worth of Bitcoin
        → Your Bitcoin exposure is 20%
        
        The bot limits exposure to each coin (usually max 10%) so you don't
        risk too much on one coin. This is called "diversification" - don't put
        all your eggs in one basket!
        """
    },
    
    "volume": {
        "simple_name": "Trading Activity",
        "short_explanation": "How many people are buying/selling right now?",
        "detailed_explanation": """
        Volume shows how much trading is happening for this coin.
        
        High volume = Lots of people buying and selling (more reliable)
        Low volume = Not many people trading (can be risky)
        
        Think of it like a busy vs empty store:
        • Busy store = You can buy/sell easily, prices are fair
        • Empty store = Hard to sell, prices might be weird
        
        The bot prefers coins with good volume for safer trades.
        """
    }
}


# ==================== TRANSLATION FUNCTIONS ====================

def translate_term(technical_term: str) -> Dict[str, str]:
    """
    Get simple explanation for any technical term.
    
    Args:
        technical_term: The jargon term to translate (e.g., "confluence_score")
    
    Returns:
        Dictionary with simple_name, explanations, etc.
    """
    term = technical_term.lower().replace(" ", "_")
    return JARGON_DICTIONARY.get(term, {
        "simple_name": technical_term,
        "short_explanation": "A trading metric",
        "detailed_explanation": "Please ask for more information about this term."
    })


def get_traffic_light(score: float, metric: str = "confluence_score") -> Tuple[str, str, str]:
    """
    Convert a numeric score to traffic light color + simple message.
    
    Args:
        score: Numeric score (0-100)
        metric: Type of metric being scored
    
    Returns:
        Tuple of (emoji, status, message)
        Example: ("🟢", "Excellent", "Great time to buy!")
    """
    term_data = JARGON_DICTIONARY.get(metric, {})
    ranges = term_data.get("ranges", {})
    
    for score_range, (emoji_status, message, *_) in ranges.items():
        if isinstance(score_range, tuple):
            min_score, max_score = score_range
            if min_score <= score <= max_score:
                emoji = emoji_status.split()[0]  # Extract just the emoji
                status = emoji_status.split(maxsplit=1)[1] if " " in emoji_status else emoji_status
                return (emoji, status, message)
        elif isinstance(score_range, str):
            # For categorical values like market regime
            continue
    
    # Default fallback
    return ("⚪", "Unknown", "No data available")


def get_regime_indicator(regime: str) -> Tuple[str, str, str]:
    """
    Get simple explanation for market regime.
    
    Args:
        regime: Market regime state (e.g., "BULL_CONFIRMED")
    
    Returns:
        Tuple of (emoji, description, explanation)
    """
    regime_data = JARGON_DICTIONARY["market_regime"]["ranges"]
    
    if regime in regime_data:
        emoji, description, explanation = regime_data[regime]
        return (emoji, description, explanation)
    
    return ("🟡", "🌥️ Unknown", "Market status is being calculated...")


def simplify_percentage(value: float, is_profit: bool = True) -> str:
    """
    Format percentage with color indicator and simple message.
    
    Args:
        value: Percentage value (e.g., 5.23)
        is_profit: True if this is profit/gain, False if loss
    
    Returns:
        Formatted string with emoji
        Example: "🟢 +5.2% (Making money!)"
    """
    if value > 0:
        emoji = "🟢" if is_profit else "🔴"
        message = "Making money!" if is_profit else "Price going up"
        return f"{emoji} +{value:.1f}% ({message})"
    elif value < 0:
        emoji = "🔴" if is_profit else "🟢"
        message = "Losing money" if is_profit else "Price going down"
        return f"{emoji} {value:.1f}% ({message})"
    else:
        return "⚪ 0.0% (No change)"


def get_signal_assessment(confluence_score: float, 
                         position_pnl_pct: Optional[float] = None) -> Dict[str, str]:
    """
    Generate informational signal assessment (NOT prescriptive commands).
    Shows what the system sees, lets user decide the action.
    
    Args:
        confluence_score: Safety score (0-100)
        position_pnl_pct: Current profit/loss percentage (if holding)
    
    Returns:
        Dictionary with signal strength, what system sees, and considerations
    """
    # For coins you don't own yet
    if position_pnl_pct is None:
        if confluence_score >= 85:
            return {
                "signal_strength": "🟢 HIGH CONVICTION",
                "emoji": "🟢",
                "what_system_sees": "All major indicators aligned positively. Strong confluence across technical, on-chain, and fundamental data.",
                "considerations": "High score indicates favorable conditions. Consider your risk tolerance and position sizing.",
                "simple_status": "Strong signal"
            }
        elif confluence_score >= 70:
            return {
                "signal_strength": "🟢 GOOD SIGNAL",
                "emoji": "🟢",
                "what_system_sees": "Most indicators positive. 3-4 out of 5 metrics showing strength.",
                "considerations": "Solid setup with minor caution areas. Review signal breakdown for specifics.",
                "simple_status": "Decent signal"
            }
        elif confluence_score >= 50:
            return {
                "signal_strength": "🟡 MIXED SIGNAL",
                "emoji": "🟡",
                "what_system_sees": "Conflicting indicators. Some positive, some negative.",
                "considerations": "Uncertainty present. May want to wait for clearer alignment or better entry.",
                "simple_status": "Unclear signal"
            }
        else:
            return {
                "signal_strength": "🔴 WEAK SIGNAL",
                "emoji": "🔴",
                "what_system_sees": "Majority of indicators showing weakness or risk.",
                "considerations": "Unfavorable conditions. Most traders would wait for improvement above 60.",
                "simple_status": "Weak signal"
            }
    
    # For coins you already own
    else:
        if position_pnl_pct >= 5:
            return {
                "signal_strength": "🟢 PROFIT TARGET ZONE",
                "emoji": "🟢",
                "what_system_sees": f"Position up {position_pnl_pct:.1f}%. In profit-taking range.",
                "considerations": "Bot will auto-exit when target hits. You can also manually close for gains.",
                "simple_status": "Making profit"
            }
        elif position_pnl_pct >= 0:
            return {
                "signal_strength": "🟡 MINOR PROFIT",
                "emoji": "🟡",
                "what_system_sees": f"Small gain of {position_pnl_pct:.1f}%. Below sell threshold.",
                "considerations": "Bot waiting for larger profit. Consider holding for target or manual exit.",
                "simple_status": "Small gain"
            }
        elif position_pnl_pct >= -5:
            return {
                "signal_strength": "🟡 MINOR DRAWDOWN",
                "emoji": "🟡",
                "what_system_sees": f"Position down {abs(position_pnl_pct):.1f}%. Within normal volatility range.",
                "considerations": "Small temporary loss. Bot holds for recovery (no stop loss). Patient approach.",
                "simple_status": "Temporary dip"
            }
        else:
            return {
                "signal_strength": "🔴 DRAWDOWN",
                "emoji": "🔴",
                "what_system_sees": f"Position down {abs(position_pnl_pct):.1f}%. Deeper than typical volatility.",
                "considerations": "Bot strategy: hold for recovery (infinite hold). You can exit manually if needed.",
                "simple_status": "In drawdown"
            }


def format_dollar_amount(amount: float, show_sign: bool = False) -> str:
    """
    Format dollar amounts in a friendly way.
    
    Args:
        amount: Dollar amount
        show_sign: Whether to show + for positive
    
    Returns:
        Formatted string like "$1,234.56" or "+$1,234.56"
    """
    if amount >= 0:
        sign = "+" if show_sign else ""
        return f"{sign}${amount:,.2f}"
    else:
        return f"-${abs(amount):,.2f}"


def explain_strategy(strategy_name: str) -> Dict[str, str]:
    """
    Explain what a trading strategy does in simple terms.
    
    Args:
        strategy_name: Name of the strategy
    
    Returns:
        Dictionary with simple explanation
    """
    strategies = {
        "Buy-the-Dip": {
            "simple_name": "Value Investor",
            "what_it_does": "Buys quality coins when they're on sale (price dropped)",
            "when_it_buys": "When a good coin drops 5-15% in price",
            "when_it_sells": "When price goes back up (+5%, +7%, or +10%)",
            "risk_level": "🟡 Medium - Holds for recovery",
            "analogy": "Like buying your favorite snack when it's on sale at the grocery store!"
        },
        "SMA Trend": {
            "simple_name": "Trend Rider",
            "what_it_does": "Follows the market direction (up or down)",
            "when_it_buys": "When the trend clearly turns upward",
            "when_it_sells": "When the trend reverses downward",
            "risk_level": "🟢 Low-Medium - Follows the crowd",
            "analogy": "Like surfing - you ride the wave until it ends!"
        },
        "Grid Bot": {
            "simple_name": "Range Trader",
            "what_it_does": "Buys low, sells high within a specific price range",
            "when_it_buys": "When price drops to lower end of range",
            "when_it_sells": "When price rises to upper end of range",
            "risk_level": "🟢 Low - Very controlled",
            "analogy": "Like a vending machine - buy at wholesale, sell at retail!"
        },
        "Hyper-Scalper": {
            "simple_name": "Speed Trader",
            "what_it_does": "Makes many small, quick trades",
            "when_it_buys": "When price dips for a few seconds",
            "when_it_sells": "When price bounces back up (even 1-2%)",
            "risk_level": "🟠 Medium-High - Fast-paced",
            "analogy": "Like a day trader on Wall Street - in and out all day!"
        }
    }
    
    return strategies.get(strategy_name, {
        "simple_name": strategy_name,
        "what_it_does": "A specialized trading approach",
        "when_it_buys": "Based on specific market conditions",
        "when_it_sells": "When profit targets are met",
        "risk_level": "🟡 Varies",
        "analogy": "Ask for more details about this strategy!"
    })


def get_signal_breakdown(score_data: Dict[str, float]) -> Dict[str, Dict[str, str]]:
    """
    Generate detailed breakdown of individual signal components.
    
    Args:
        score_data: Dict with technical_score, onchain_score, macro_score, fundamental_score
    
    Returns:
        Dict mapping each component to its assessment
    """
    breakdown = {}
    
    components = [
        ("technical_score", "Price Health", "Technical indicators (RSI, moving averages, volume)"),
        ("onchain_score", "Smart Money", "Blockchain data (whale movements, exchange flows)"),
        ("macro_score", "Market Mood", "Overall market regime and risk environment"),
        ("fundamental_score", "Fundamentals", "Long-term value drivers (adoption, development)")
    ]
    
    for key, name, description in components:
        value = score_data.get(key, 0)
        emoji, status, _ = get_traffic_light(value, "confluence_score")
        
        breakdown[name] = {
            "score": value,
            "emoji": emoji,
            "status": status,
            "description": description
        }
    
    return breakdown


# ==================== BEGINNER MODE DETECTOR ====================

def should_show_beginner_mode(user_session: Optional[dict] = None) -> bool:
    """
    Determine if beginner mode should be enabled.
    Default: YES (beginner mode default ON)
    
    Args:
        user_session: User session data with preferences
    
    Returns:
        True if beginner mode should be shown
    """
    if user_session is None:
        return True  # Default to beginner mode
    
    return user_session.get("beginner_mode", True)


if __name__ == "__main__":
    # Test the functions
    print("=== Testing Beginner Helpers (Refactored) ===")
    print()
    
    # Test translation
    print("1. Confluence Score Translation:")
    print(translate_term("confluence_score")["simple_name"])
    print()
    
    # Test traffic light
    print("2. Traffic Light System:")
    for score in [95, 75, 55, 35, 15]:
        emoji, status, message = get_traffic_light(score)
        print(f"Score {score}: {emoji} {status} - {message}")
    print()
    
    # Test signal assessments (not recommendations)
    print("3. Signal Assessments (Not Commands):")
    sig = get_signal_assessment(85)
    print(f"New coin (score 85): {sig['signal_strength']}")
    print(f"  What system sees: {sig['what_system_sees']}")
    print(f"  Considerations: {sig['considerations']}")
    print()
    
    sig = get_signal_assessment(45, position_pnl_pct=-8.5)
    print(f"Held coin (down 8.5%): {sig['signal_strength']}")
    print(f"  What system sees: {sig['what_system_sees']}")
    print()
    
    # Test regime
    print("4. Market Regime:")
    emoji, desc, explain = get_regime_indicator("BULL_CONFIRMED")
    print(f"{emoji} {desc}")
    print(f"   → {explain}")
    print()
    
    # Test signal breakdown
    print("5. Signal Breakdown:")
    breakdown = get_signal_breakdown({
        "technical_score": 85,
        "onchain_score": 78,
        "macro_score": 65,
        "fundamental_score": 82
    })
    for name, data in breakdown.items():
        print(f"{data['emoji']} {name}: {data['score']}/100 - {data['status']}")
