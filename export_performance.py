#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automated Performance Export Script - CryptoIntel Hub
Generates daily performance reports including Intelligence (Pillar C) data
Run this on your VPS via cron to automate monitoring

Exports:
- Pillar B: Bot trading performance (MEXC)
- Pillar C: Intelligence scoring data (Confluence V2 + Regulatory Scorer)
- Pillar A: Luno monitor status (if available)
"""
import sys
import os
import json
from datetime import datetime, timedelta
from pathlib import Path

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import Database, Position, Trade, BotStatus, ConfluenceScore, PortfolioSnapshot
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker

def export_performance_report(db_path='data/trades_v3.db', output_dir='performance_reports'):
    """
    Export comprehensive performance data to JSON files
    """
    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # Initialize database
    db = Database(db_path=db_path)
    session = db.get_session()

    timestamp = datetime.utcnow()
    report_date = timestamp.strftime('%Y-%m-%d')

    print(f"📊 Generating Performance Report for {report_date}")
    print("=" * 60)

    # ==========================================
    # 1. OPEN POSITIONS SNAPSHOT
    # ==========================================
    open_positions = session.query(Position).filter(
        Position.status == 'OPEN'
    ).all()

    positions_data = []
    total_unrealized_pnl = 0
    total_position_value = 0

    for pos in open_positions:
        pos_data = {
            'position_id': pos.id,
            'bot_id': pos.bot_id,
            'symbol': pos.symbol,
            'entry_date': pos.entry_date.isoformat() if pos.entry_date else None,
            'entry_price': pos.entry_price,
            'current_price': pos.current_price,
            'position_size_usd': pos.position_size_usd,
            'amount': pos.amount,
            'unrealized_pnl_pct': pos.unrealized_pnl_pct,
            'unrealized_pnl_usd': pos.unrealized_pnl_usd,
            'days_held': (timestamp - pos.entry_date).days if pos.entry_date else 0,
            'exchange': getattr(pos, 'exchange', 'MEXC')  # Handle legacy DBs without exchange column
        }
        positions_data.append(pos_data)

        if pos.unrealized_pnl_usd:
            total_unrealized_pnl += pos.unrealized_pnl_usd
        if pos.position_size_usd:
            total_position_value += pos.position_size_usd

    print(f"✅ Open Positions: {len(open_positions)}")
    print(f"   Total Position Value: ${total_position_value:.2f}")
    print(f"   Total Unrealized P&L: ${total_unrealized_pnl:.2f}")

    # ==========================================
    # 2. RECENT TRADES (Last 7 days)
    # ==========================================
    seven_days_ago = timestamp - timedelta(days=7)

    recent_trades = session.query(Trade).filter(
        Trade.timestamp >= seven_days_ago
    ).order_by(desc(Trade.timestamp)).all()

    trades_data = []
    for trade in recent_trades:
        trades_data.append({
            'timestamp': trade.timestamp.isoformat() if trade.timestamp else None,
            'strategy': trade.strategy,
            'symbol': trade.symbol,
            'side': trade.side,
            'price': trade.price,
            'amount': trade.amount,
            'cost': trade.cost,
            'fee': trade.fee,
            'exchange': getattr(trade, 'exchange', 'MEXC')  # Handle legacy DBs
        })

    print(f"✅ Recent Trades (7 days): {len(recent_trades)}")

    # ==========================================
    # 3. BOT STATUS SUMMARY
    # ==========================================
    bot_statuses = session.query(BotStatus).all()

    bots_data = []
    total_pnl_all_bots = 0

    for bot in bot_statuses:
        bot_data = {
            'strategy': bot.strategy,
            'status': bot.status,
            'started_at': bot.started_at.isoformat() if bot.started_at else None,
            'last_heartbeat': bot.last_heartbeat.isoformat() if bot.last_heartbeat else None,
            'total_trades': bot.total_trades,
            'total_pnl': bot.total_pnl,
            'wallet_balance': bot.wallet_balance
        }
        bots_data.append(bot_data)

        if bot.total_pnl:
            total_pnl_all_bots += bot.total_pnl

    print(f"✅ Active Bots: {len(bot_statuses)}")
    print(f"   Total Realized P&L: ${total_pnl_all_bots:.2f}")

    # ==========================================
    # 4. PORTFOLIO EQUITY SNAPSHOT
    # ==========================================
    latest_snapshot = session.query(PortfolioSnapshot).order_by(
        desc(PortfolioSnapshot.timestamp)
    ).first()

    portfolio_data = None
    if latest_snapshot:
        portfolio_data = {
            'timestamp': latest_snapshot.timestamp.isoformat(),
            'total_equity_usd': latest_snapshot.total_equity_usd,
            'cash_balance_usd': latest_snapshot.cash_balance_usd,
            'active_positions_value_usd': latest_snapshot.active_positions_value_usd,
            'unrealized_pnl_usd': latest_snapshot.unrealized_pnl_usd,
            'active_positions_count': latest_snapshot.active_positions_count
        }
        print(f"✅ Portfolio Equity: ${latest_snapshot.total_equity_usd:.2f}")

    # ==========================================
    # 5. CLOSED TRADES SUMMARY (Last 30 days)
    # ==========================================
    thirty_days_ago = timestamp - timedelta(days=30)

    closed_positions = session.query(Position).filter(
        Position.status == 'CLOSED',
        Position.updated_at >= thirty_days_ago
    ).all()

    wins = 0
    losses = 0
    total_realized_pnl = 0

    for pos in closed_positions:
        # Get final trade for this position
        final_trade = session.query(Trade).filter(
            Trade.position_id == pos.id,
            Trade.side == 'SELL'
        ).order_by(desc(Trade.timestamp)).first()

        if final_trade:
            # Calculate P&L (simplified)
            buy_trades = session.query(Trade).filter(
                Trade.position_id == pos.id,
                Trade.side == 'BUY'
            ).all()

            total_cost = sum(t.cost for t in buy_trades)
            total_revenue = final_trade.cost
            pnl = total_revenue - total_cost - final_trade.fee

            total_realized_pnl += pnl

            if pnl > 0:
                wins += 1
            else:
                losses += 1

    win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0

    print(f"✅ Closed Trades (30 days): {wins + losses}")
    print(f"   Wins: {wins} | Losses: {losses} | Win Rate: {win_rate:.1f}%")
    print(f"   Realized P&L: ${total_realized_pnl:.2f}")

    # ==========================================
    # 6. INTELLIGENCE DATA (Pillar C)
    # ==========================================
    intelligence_data = None
    try:
        # Check if intelligence.db exists
        intel_db_path = 'intelligence.db'
        if os.path.exists(intel_db_path):
            intel_engine = create_engine(f'sqlite:///{intel_db_path}', echo=False)
            IntelSession = sessionmaker(bind=intel_engine)
            intel_session = IntelSession()

            # Query latest regulatory scores
            from sqlalchemy import Table, MetaData
            metadata = MetaData()
            metadata.reflect(bind=intel_engine)

            if 'regulatory_scores' in metadata.tables:
                regulatory_table = metadata.tables['regulatory_scores']

                # Get latest scores for each asset
                latest_scores_query = """
                SELECT symbol, score, confidence, recommendation,
                       timestamp, regulatory_score, institutional_score,
                       ecosystem_score, market_score
                FROM regulatory_scores
                WHERE id IN (
                    SELECT MAX(id)
                    FROM regulatory_scores
                    GROUP BY symbol
                )
                ORDER BY score DESC
                """

                results = intel_engine.execute(latest_scores_query)

                regulatory_scores = []
                for row in results:
                    regulatory_scores.append({
                        'symbol': row[0],
                        'total_score': row[1],
                        'confidence': row[2],
                        'recommendation': row[3],
                        'timestamp': row[4],
                        'breakdown': {
                            'regulatory': row[5],
                            'institutional': row[6],
                            'ecosystem': row[7],
                            'market': row[8]
                        }
                    })

                intelligence_data = {
                    'regulatory_scores': regulatory_scores,
                    'total_assets_scored': len(regulatory_scores)
                }

                print(f"✅ Intelligence Data: {len(regulatory_scores)} assets scored")

            intel_session.close()
        else:
            print("⚠️  Intelligence database not found (Pillar C inactive)")

    except Exception as e:
        print(f"⚠️  Could not load intelligence data: {e}")
        intelligence_data = None

    # ==========================================
    # 7. BUILD FINAL REPORT
    # ==========================================
    report = {
        'report_date': report_date,
        'generated_at': timestamp.isoformat(),
        'system_version': '2025.12.25',
        'three_pillar_status': {
            'pillar_a_luno': 'Monitoring (Manual)',
            'pillar_b_trading': 'Active (MEXC Paper)',
            'pillar_c_intelligence': 'Active' if intelligence_data else 'Inactive'
        },
        'summary': {
            'total_equity': portfolio_data['total_equity_usd'] if portfolio_data else 0,
            'open_positions_count': len(open_positions),
            'total_position_value': total_position_value,
            'unrealized_pnl': total_unrealized_pnl,
            'realized_pnl_30d': total_realized_pnl,
            'total_pnl_all_time': total_pnl_all_bots,
            'win_rate_30d': win_rate,
            'wins_30d': wins,
            'losses_30d': losses
        },
        'open_positions': positions_data,
        'recent_trades_7d': trades_data,
        'bot_statuses': bots_data,
        'portfolio_snapshot': portfolio_data,
        'intelligence': intelligence_data
    }

    # ==========================================
    # 8. SAVE REPORT FILES
    # ==========================================

    # Daily report (gets overwritten each day)
    daily_file = output_path / 'latest_performance.json'
    with open(daily_file, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"\n✅ Saved: {daily_file}")

    # Historical archive (dated files)
    archive_file = output_path / f'performance_{report_date}.json'
    with open(archive_file, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"✅ Saved: {archive_file}")

    # Human-readable summary
    summary_file = output_path / 'summary.txt'
    with open(summary_file, 'w') as f:
        f.write(f"Crypto Bot Performance Summary\n")
        f.write(f"Generated: {timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        f.write(f"=" * 60 + "\n\n")

        f.write(f"PORTFOLIO OVERVIEW\n")
        f.write(f"-" * 60 + "\n")
        if portfolio_data:
            f.write(f"Total Equity:        ${portfolio_data['total_equity_usd']:,.2f}\n")
            f.write(f"Cash Balance:        ${portfolio_data['cash_balance_usd']:,.2f}\n")
            f.write(f"Positions Value:     ${portfolio_data['active_positions_value_usd']:,.2f}\n")
            f.write(f"Unrealized P&L:      ${portfolio_data['unrealized_pnl_usd']:,.2f}\n")
        f.write(f"\n")

        f.write(f"OPEN POSITIONS ({len(open_positions)})\n")
        f.write(f"-" * 60 + "\n")
        f.write(f"Total Position Value: ${total_position_value:,.2f}\n")
        f.write(f"Total Unrealized P&L: ${total_unrealized_pnl:,.2f}\n")
        f.write(f"\n")

        f.write(f"PERFORMANCE (Last 30 Days)\n")
        f.write(f"-" * 60 + "\n")
        f.write(f"Closed Trades:       {wins + losses}\n")
        f.write(f"Wins:                {wins}\n")
        f.write(f"Losses:              {losses}\n")
        f.write(f"Win Rate:            {win_rate:.1f}%\n")
        f.write(f"Realized P&L:        ${total_realized_pnl:,.2f}\n")
        f.write(f"\n")

        f.write(f"BOT STATUS\n")
        f.write(f"-" * 60 + "\n")
        for bot in bots_data:
            f.write(f"{bot['strategy']:<30} | Trades: {bot['total_trades']:>4} | P&L: ${bot['total_pnl']:>8.2f}\n")
        f.write(f"\n")

        # Intelligence section
        if intelligence_data and intelligence_data.get('regulatory_scores'):
            f.write(f"INTELLIGENCE SCORES (Pillar C)\n")
            f.write(f"-" * 60 + "\n")
            for score in intelligence_data['regulatory_scores']:
                f.write(f"{score['symbol']:<12} | Score: {score['total_score']:>3.0f}/100 | {score['recommendation']:<10} | {score['confidence']}\n")
            f.write(f"\n")
            f.write(f"Total Assets Scored: {intelligence_data['total_assets_scored']}\n")

    print(f"✅ Saved: {summary_file}")

    session.close()

    print("\n" + "=" * 60)
    print("✅ Performance export completed successfully!")
    print(f"📁 Reports saved to: {output_path.absolute()}")
    print("=" * 60)

    return report

if __name__ == "__main__":
    # Check for command line arguments
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'data/trades_v3.db'
    output_dir = sys.argv[2] if len(sys.argv) > 2 else 'performance_reports'

    try:
        export_performance_report(db_path=db_path, output_dir=output_dir)
    except Exception as e:
        print(f"❌ Error generating performance report: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
