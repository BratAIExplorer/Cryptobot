# Deploy Intelligence System to VPS (Fixed)
# Run this from Windows PowerShell

$VPS_USER = "root"
$VPS_IP = "72.60.40.29"
$VPS_PATH = "/Antigravity/antigravity/scratch/crypto_trading_bot"

Write-Host "🚀 Starting Deployment to VPS (${VPS_IP})..." -ForegroundColor Cyan

# 1. Upload Intelligence Folder
Write-Host "📦 Uploading intelligence system..." -ForegroundColor Yellow
scp -r .\intelligence "${VPS_USER}@${VPS_IP}:${VPS_PATH}/"

# 2. Upload Documentation
Write-Host "📄 Uploading documentation..." -ForegroundColor Yellow
scp CRYPTOINTEL_HUB_STATUS.md "${VPS_USER}@${VPS_IP}:${VPS_PATH}/"
scp CONFLUENCE_HYBRID_WATCHLIST_DOCUMENTATION.md "${VPS_USER}@${VPS_IP}:${VPS_PATH}/"

# 3. Create docs directory on VPS and upload master docs
Write-Host "📚 Uploading master architecture docs..." -ForegroundColor Yellow
ssh "${VPS_USER}@${VPS_IP}" "mkdir -p ${VPS_PATH}/docs"
scp C:\Users\user\.gemini\antigravity\brain\85792ad5-2f70-4aa8-9f10-3c82e016d404\MASTER_ARCHITECTURE.md "${VPS_USER}@${VPS_IP}:${VPS_PATH}/docs/"
scp C:\Users\user\.gemini\antigravity\brain\85792ad5-2f70-4aa8-9f10-3c82e016d404\SYSTEM_REFERENCE.md "${VPS_USER}@${VPS_IP}:${VPS_PATH}/docs/"
scp C:\Users\user\.gemini\antigravity\brain\85792ad5-2f70-4aa8-9f10-3c82e016d404\DEPLOYMENT_GUIDE.md "${VPS_USER}@${VPS_IP}:${VPS_PATH}/docs/"

Write-Host "✅ Deployment Complete!" -ForegroundColor Green
Write-Host "---------------------------------------------------"
Write-Host "To run the dashboard on VPS:"
Write-Host "1. ssh root@72.60.40.29"
Write-Host "2. cd /Antigravity/antigravity/scratch/crypto_trading_bot"
Write-Host "3. python3 -m pip install plotly  (if needed)"
Write-Host "4. streamlit run intelligence/dashboard_intelligence.py --server.port 8502"
Write-Host "---------------------------------------------------"
