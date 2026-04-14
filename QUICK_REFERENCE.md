# Azure Migration - Quick Reference Card

## 🚀 Quick Start (10 minutes)

### 1. Create Azure Resource
- Visit: https://portal.azure.com
- Create: Speech Service (Free F0 tier)
- Region: eastus (or closest to users)

### 2. Get Credentials
- Keys and Endpoint → Copy KEY 1
- Location/Region → Copy region name

### 3. Configure .env
```bash
AZURE_SPEECH_KEY=paste_key_here
AZURE_SPEECH_REGION=eastus
PHONEME_BACKEND=auto
```

### 4. Deploy
```bash
cd backend
pip install -r requirements.txt
python main.py
```

### 5. Verify
Look for: `✅ Azure Pronunciation Assessment loaded successfully`

---

## 💰 Cost Savings

| Item | Before | After | Savings |
|------|--------|-------|---------|
| Monthly | $30 | $0 | $30 |
| Annual | $360 | $0 | $360 |

**Free Tier**: 5 hours/month  
**Your Usage**: <5 hours/month  
**Cost**: $0/month

---

## ⚡ Performance

| Metric | Before | After |
|--------|--------|-------|
| Latency | ~3s | ~0.5-1s |
| Accuracy | Good | Excellent |
| Uptime | 95% | 99.9% |

---

## 🔧 Configuration Options

### Auto Mode (Recommended)
```bash
PHONEME_BACKEND=auto
```
Tries Azure → Falls back to ONNX if needed

### Azure Only
```bash
PHONEME_BACKEND=azure
```
Forces Azure (fails if not configured)

### Legacy (ONNX)
```bash
PHONEME_BACKEND=onnx
```
Self-hosted only

---

## 🧪 Testing

```bash
# Run integration tests
cd backend
python test_azure_integration.py

# Expected output:
✅ PASS     Credentials
✅ PASS     Azure Extractor
✅ PASS     PhonemeAssistant
```

---

## 📊 Monitoring

### Check Backend
```bash
# Server logs should show:
Phoneme backend initialized: azure
```

### Azure Portal
1. Navigate to Speech Service
2. Metrics → Transactions, Audio Length
3. Set alert at 4 hours/month

---

## 🔄 Rollback

### Option 1: Quick Disable
```bash
PHONEME_BACKEND=onnx
# Restart server
```

### Option 2: Remove Credentials
```bash
# Comment out in .env:
# AZURE_SPEECH_KEY=...
# With auto mode, falls back to ONNX
```

---

## ⚠️ Troubleshooting

### "AZURE_SPEECH_KEY not set"
→ Check .env file, verify key is set

### "Authentication failed"
→ Verify key in Azure Portal, try KEY 2

### "Recognition canceled"
→ Check audio quality, network connection

### High latency
→ Choose closer Azure region

---

## 📚 Documentation

- **Setup**: AZURE_SETUP_GUIDE.md
- **Migration**: MIGRATION_PLAN.md
- **Costs**: COST_SAVINGS_ANALYSIS.md
- **Research**: research_phoneme_transcription_apis.md

---

## ✅ Deployment Checklist

- [ ] Create Azure account
- [ ] Create Speech Service (Free tier)
- [ ] Get KEY and REGION
- [ ] Update .env file
- [ ] Install dependencies
- [ ] Run tests
- [ ] Deploy to production
- [ ] Monitor for 1 week
- [ ] Decommission old server
- [ ] Save $30/month! 🎉

---

## 🎯 Success Criteria

After deployment, verify:
- ✅ Logs show: `backend: azure`
- ✅ Latency < 1.5s (down from 3s)
- ✅ No error rate increase
- ✅ Azure usage < 5 hrs/month
- ✅ Old server can be shut down

---

## 🆘 Support

**Issue**: Check logs first  
**Credentials**: Azure Portal → Keys  
**Service Status**: https://status.azure.com/  
**Emergency**: Set `PHONEME_BACKEND=onnx`

---

## 📞 Quick Links

- Azure Portal: https://portal.azure.com
- Free Tier: https://azure.microsoft.com/free/
- Speech Docs: https://learn.microsoft.com/azure/cognitive-services/speech-service/
- Status Page: https://status.azure.com/

---

**Time to Deploy**: 40 minutes  
**Time to ROI**: Immediate  
**Annual Savings**: $360  
**Risk**: Low (auto-fallback)  

✅ **Ready to Deploy!**
