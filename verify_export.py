from core.logger import TradeLogger
import os

logger = TradeLogger()
print("Generating reports...")
tax, audit = logger.export_compliance_reports()

print(f"\nTax Report: {tax}")
print(f"Audit Log: {audit}")

if tax and os.path.exists(tax):
    print("✅ Tax Report exists.")
else:
    print("❌ Tax Report missing.")

if audit and os.path.exists(audit):
    print("✅ Audit Log exists.")
else:
    print("❌ Audit Log missing.")
