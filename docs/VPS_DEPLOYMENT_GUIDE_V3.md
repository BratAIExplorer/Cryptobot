# 🚀 VPS Deployment Guide (V3 Architecture)

**Objective**: Deploy the new "Safety-First" V3 bots to a separate directory on your VPS, allowing them to run alongside legacy bots if needed.

---

## 📂 Architecture Check
*   **Legacy Path**: `~/crypto_bot` (Existing bots running here)
*   **New V3 Path**: `~/cryptobot_v3` (New bots will run here)
*   **Isolation**: File systems are separate. Databases are separate.

---

## 🛠️ Step 1: Preparation (Local)

1.  **Stop Local Paper Bots**:
    ```powershell
    # Press Ctrl+C in your terminal to stop the local test.
    ```

2.  **Verify Configuration**:
    Ensure `run_bot.py` has:
    *   `exchange=['BINANCE']`
    *   `initial_balance=250` (for Grid)

---

## 📤 Step 2: Upload Code (From Local Windows)

Run this PowerShell command to upload the code to the new directory. 
*(Replace `user` and `your_vps_ip` with your actual details)*

```powershell
# 1. Create the new directory on VPS
ssh user@your_vps_ip "mkdir -p ~/cryptobot_v3"

# 2. Upload files (excluding data/env to prevent overwrite/leak)
scp -r core strategies utils scripts docs *.py requirements.txt user@your_vps_ip:~/cryptobot_v3/
```

---

## 🔧 Step 3: Setup & Launch (On VPS)

Connect to your VPS:
```bash
ssh user@your_vps_ip
```

Then run these commands inside the VPS:

```bash
# 1. Go to new directory
cd ~/cryptobot_v3

# 2. Create Virtual Environment (Isolated from old bot)
python3 -m venv venv
source venv/bin/activate

# 3. Install Dependencies
pip install -r requirements.txt

# 4. Create .env file (Or copy from old bot if keys are same)
# Option A: Create new
nano .env 
# (Paste BINANCE_API_KEY=... and BINANCE_SECRET_KEY=...)

# Option B: Copy from old bot (Easier)
cp ~/crypto_bot/.env ~/cryptobot_v3/

# 5. Run Pre-Flight Check
python scripts/go_no_go.py
# (Output should say: "✅ GO! System is Ready for Launch")

# 6. Start the Bots (Live Mode)
python run_bot.py --mode live
```

---

## ❓ FAQ: Parallel Execution

**Q: Can existing bots continue running in `~/crypto_bot`?**
**A: YES.**
The new V3 bots run in `~/cryptobot_v3`. They have their own:
*   `venv` (Python environment)
*   `trades.db` (Database)
*   `logs`

**⚠️ CAUTION: Shared API Limits**
Both bots share the **same Binance Account API Key**.
*   **Risk**: If both bots try to trade *aggressively* at the exact same second, you might hit a "Rate Limit" error.
*   **Mitigation**: The new V3 bots are "Chill" (Grid = Passive, Dip = Wait for crash). The risk is low.
*   **Money**: Ensure you have enough USDT in the account for *both* the old bots' active orders AND the new $250 + $250 + $1000 allocation.

**Recommendation**:
If the old bots are profitable, keep them. If they are the ones you wanted to replace, stop them via `pm2 stop <id>` to free up capital.
