"""
Test XRP Profit Calculation
Verifies currency fix is working correctly
"""
from src.luno_client import LunoClient
from src.price_monitor import PriceMonitor

client = LunoClient()
pm = PriceMonitor()

# Get XRP data
ticker = client.get_ticker('XRPMYR')
avg, amt, count = client.calculate_average_buy_price('XRP')
current = ticker['last_trade']
pl = pm.calculate_profit_loss('XRP', avg, current)

print("=" * 60)
print("XRP PROFIT/LOSS TEST")
print("=" * 60)
print(f"Current Price:      RM {current:,.2f}")
print(f"Average Buy Price:  RM {avg:,.2f}")
print(f"Total Amount:       {amt:,.2f} XRP")
print(f"Transaction Count:  {count}")
print(f"-" * 60)
print(f"Profit/Loss:        RM {pl['profit_loss_myr']:,.2f}")
print(f"Profit/Loss %:      {pl['profit_loss_percent']:+.2f}%")
print(f"Status:             {pl['status'].upper()}")
print("=" * 60)

# Expected: LOSS (bought at ~RM 10.52, current ~RM 8.07 = -23% loss)
