# Azure Pronunciation Assessment Setup Guide

This guide explains how to switch from the self-hosted ONNX backend to Azure Pronunciation Assessment API for better cost-effectiveness and accuracy.

## Why Switch to Azure?

### Cost Comparison
- **Current (ONNX)**: $30/month for 2vCPU server + 3s latency
- **Azure API**: $0/month (within 5 hours/month free tier) + 0.5-1s latency
- **Break-even**: ~150-200 hours/month of usage

### Benefits
- ✅ **$30/month cost savings** (within free tier limits)
- ✅ **Faster response times** (~0.5-1s vs ~3s)
- ✅ **Better accuracy** (purpose-built for pronunciation assessment)
- ✅ **No server management** (cloud-based with SLA)
- ✅ **Phoneme-level accuracy scores** (additional insights)
- ✅ **Auto-scaling** (handles traffic spikes)

## Setup Instructions

### 1. Create Azure Account

1. Visit [https://azure.microsoft.com/free/](https://azure.microsoft.com/free/)
2. Sign up for a free account (includes $200 credit for 30 days)
3. No credit card required for free tier services

### 2. Create Speech Service Resource

1. Go to [Azure Portal](https://portal.azure.com)
2. Click "Create a resource"
3. Search for "Speech" and select "Speech Services"
4. Click "Create"
5. Fill in the form:
   - **Subscription**: Your subscription
   - **Resource group**: Create new or select existing
   - **Region**: Choose closest to your users (e.g., `eastus`, `westus2`, `westeurope`)
   - **Name**: Choose a unique name (e.g., `wordwizai-speech`)
   - **Pricing tier**: Select **Free F0** (5 hours/month free)
6. Click "Review + create" → "Create"

### 3. Get Your Credentials

1. Once created, go to your Speech Service resource
2. In the left menu, click "Keys and Endpoint"
3. Copy:
   - **KEY 1** (or KEY 2) → This is your `AZURE_SPEECH_KEY`
   - **Location/Region** → This is your `AZURE_SPEECH_REGION`

### 4. Configure Environment Variables

Update your `.env` file (or create one based on `.env.example`):

```bash
# Azure Speech Services Configuration
AZURE_SPEECH_KEY=your_key_here
AZURE_SPEECH_REGION=eastus

# Phoneme Backend (auto = try Azure first, fallback to ONNX)
PHONEME_BACKEND=auto
```

### 5. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This will install `azure-cognitiveservices-speech` and other dependencies.

### 6. Restart Your Server

```bash
cd backend
python main.py
```

You should see:
```
Initializing Azure Pronunciation Assessment (region: eastus)...
✅ Azure Pronunciation Assessment loaded successfully
Phoneme backend initialized: azure
```

## Configuration Options

### Backend Selection

Set the `PHONEME_BACKEND` environment variable:

#### Auto Mode (Recommended)
```bash
PHONEME_BACKEND=auto
```
- Tries Azure first (if credentials available)
- Falls back to ONNX if Azure fails or credentials missing
- **Best for production**: Cost-effective with reliability

#### Azure Only
```bash
PHONEME_BACKEND=azure
```
- Forces Azure backend
- Fails if credentials not configured
- Use for testing or when you want to ensure Azure is used

#### ONNX/PyTorch (Legacy)
```bash
PHONEME_BACKEND=onnx
# or
PHONEME_BACKEND=pytorch
```
- Uses self-hosted models
- More expensive (requires dedicated server)
- Use only if Azure is unavailable in your region

## Usage Monitoring

### Check Current Backend

The system logs which backend is being used:
```
Initializing Azure Pronunciation Assessment (region: eastus)...
✅ Azure Pronunciation Assessment loaded successfully
Phoneme backend initialized: azure
```

### Monitor Azure Usage

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to your Speech Service resource
3. Click "Metrics" in the left menu
4. Select "Transactions" to see API calls
5. Select "Audio Length" to see hours used

**Free Tier Limits:**
- 5 hours/month of audio processed
- 20 transactions per minute

### Cost Estimates

Based on typical usage patterns:

| Users/Month | Avg Usage/User | Monthly Hours | Cost |
|-------------|----------------|---------------|------|
| 100 | 5 minutes | 8.3 hours | **$0** (free tier) |
| 500 | 5 minutes | 41.7 hours | ~$4 over free tier = **~$4/month** |
| 1,000 | 5 minutes | 83.3 hours | ~$78 over free tier = **~$78/month** |

**Still cheaper than $30/month server for <100 users!**

## Troubleshooting

### "AZURE_SPEECH_KEY not set"

**Problem**: Environment variable not configured.

**Solution**: 
1. Check your `.env` file exists in `backend/` directory
2. Verify `AZURE_SPEECH_KEY=your_actual_key` is set
3. Restart the server

### "Authentication failed"

**Problem**: Invalid credentials.

**Solution**:
1. Verify your key is correct (check Azure Portal)
2. Ensure no extra spaces in the key
3. Try using KEY 2 if KEY 1 doesn't work

### "Region not supported"

**Problem**: Invalid or unavailable region.

**Solution**:
1. Check [supported regions](https://learn.microsoft.com/en-us/azure/cognitive-services/speech-service/regions)
2. Use common regions: `eastus`, `westus2`, `westeurope`, `southeastasia`
3. Update `AZURE_SPEECH_REGION` in `.env`

### "Recognition canceled"

**Problem**: Audio quality issues or network problems.

**Solution**:
1. Check audio is clear and not too quiet
2. Verify network connectivity
3. Check Azure service status
4. System will automatically fallback to ONNX if `PHONEME_BACKEND=auto`

### High Latency

**Problem**: Slower than expected response times.

**Solution**:
1. Choose Azure region closest to your users
2. Check network latency to Azure
3. Verify you're on a good network connection
4. Azure typically: 200-500ms (vs 3s for ONNX on 2vCPU)

## Migration Checklist

- [ ] Create Azure account
- [ ] Create Speech Service resource (Free tier)
- [ ] Get credentials (KEY and REGION)
- [ ] Update `.env` file with credentials
- [ ] Set `PHONEME_BACKEND=auto` (or `azure`)
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Restart server
- [ ] Verify Azure backend is loaded (check logs)
- [ ] Test with sample audio
- [ ] Monitor usage in Azure Portal
- [ ] **Decommission old 2vCPU server** ($30/month savings!)

## Rollback Plan

If you need to rollback to ONNX:

1. Set environment variable:
   ```bash
   PHONEME_BACKEND=onnx
   ```
2. Restart server
3. System will use self-hosted ONNX backend

Or simply remove Azure credentials:
```bash
# Comment out or remove these lines from .env
# AZURE_SPEECH_KEY=...
# AZURE_SPEECH_REGION=...
```

With `PHONEME_BACKEND=auto`, system will automatically fallback to ONNX.

## FAQs

### Do I need to keep the ONNX server running?

**No!** Once Azure is configured and working:
1. Verify Azure backend is active
2. Test with production traffic
3. Shut down the 2vCPU server
4. **Save $30/month!**

Keep ONNX as fallback option in code (already configured with `PHONEME_BACKEND=auto`).

### What happens if I exceed the free tier?

Azure automatically starts charging $1.30/hour after 5 hours/month. Monitor usage in Azure Portal. Set up billing alerts to avoid surprises.

### Can I use multiple regions?

Yes! You can create multiple Speech Service resources in different regions and route users to the closest one. Update `AZURE_SPEECH_REGION` dynamically based on user location.

### What about data privacy?

Azure Speech Services:
- ✅ GDPR compliant
- ✅ Audio not stored by default
- ✅ Microsoft Privacy Statement applies
- ⚠️ Audio sent to cloud (vs on-premise with ONNX)

For highly sensitive use cases, you may prefer ONNX self-hosted option.

## Support

For issues:
1. Check logs: `Phoneme backend initialized: azure` should appear
2. Verify credentials in Azure Portal
3. Check Azure service status: [https://status.azure.com/](https://status.azure.com/)
4. Review Azure Speech Services docs: [https://learn.microsoft.com/azure/cognitive-services/speech-service/](https://learn.microsoft.com/azure/cognitive-services/speech-service/)

## Summary

✅ **Cost savings**: $30/month → $0/month (within free tier)  
✅ **Better performance**: 3s → 0.5-1s latency  
✅ **Higher accuracy**: Purpose-built pronunciation assessment  
✅ **Easy setup**: ~10 minutes to configure  
✅ **Auto-fallback**: Fallback to ONNX if Azure unavailable  

**Recommendation**: Start with `PHONEME_BACKEND=auto` to get the best of both worlds - Azure's cost and performance when available, ONNX as reliable fallback.
