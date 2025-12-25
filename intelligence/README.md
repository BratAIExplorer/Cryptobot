# Multi-Asset Intelligence System

A parallel scoring system for cryptocurrency assets that complements Confluence V2.

## Purpose

Different cryptocurrencies are driven by different factors:
- **BTC, ETH, DOGE**: Technical patterns (RSI, SMA, volume) → Use Confluence V2
- **XRP, ADA, SOL**: Regulatory progress, institutional adoption → Use Regulatory Scorer

This system automatically routes each asset to the appropriate scoring method.

## Quick Example

**XRP Scoring**:
- Confluence V2: **1.8/100** (AVOID) - RSI is neutral, price below SMA200
- Regulatory: **70.0/100** (BUY) - SEC won, ETFs approved, banks adopting

The 68-point difference shows why you need both systems!

## Usage

```bash
# Score XRP (uses regulatory metrics)
python -m intelligence.regulatory_scorer

# Check asset classification
python -m intelligence.asset_classifier

# Verify bot safety
python intelligence\scripts\verify_bot_health.py
```

## Safety

✅ Completely isolated in `intelligence/` folder  
✅ Separate database (`intelligence.db`)  
✅ Zero modifications to existing bot code  
✅ All feature flags OFF by default  
✅ 30-second rollback (delete folder)  

## Documentation

- `QUICK_START.md` - How to use it now
- `../brain/../implementation_plan.md` - Full technical details
- `../brain/../walkthrough.md` - Test results and proof of concept

## Current Status

**✅ DEPLOYED & TESTED**
- AssetClassifier: Routing 11 assets correctly
- RegulatoryScorer: XRP scores 70/100 (BUY,HIGH confidence)
- Bot Health: All safety checks passed
- Ready for use in XRP investment decision

---

**Built by**: CryptoIntel Hub  
**Version**: 1.0.0  
**Status**: Production-ready for manual scoring
