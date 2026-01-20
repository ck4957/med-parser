# 🔧 Quick Troubleshooting Guide - MLX Medical Parser

**Save this for when things go wrong!**

---

## 🚨 Common Issues & Instant Fixes

### Issue 1: "ImportError: No module named 'mlx'"

**Symptom:**
```python
ImportError: No module named 'mlx'
```

**Quick Fix:**
```bash
# Verify you're on Apple Silicon
uname -m  # Must show: arm64

# If arm64:
pip uninstall mlx mlx-lm
pip install mlx-lm --no-cache-dir --upgrade

# If x86_64 (Intel Mac):
# MLX won't work. Use Ollama instead:
brew install ollama
ollama pull medllama2
```

**Root Cause:** MLX only works on Apple Silicon (M1/M2/M3/M4)

---

### Issue 2: "Out of memory" during model load

**Symptom:**
```
Killed: 9
```
or
```
MemoryError: Cannot allocate memory
```

**Quick Fix (Option 1 - Free memory):**
```bash
# Close memory hogs
pkill -f "Google Chrome"
pkill -f "Slack"
pkill -f "Docker"

# Check available memory
python3 -c "import psutil; print(f'{psutil.virtual_memory().available / 1e9:.1f} GB free')"

# Restart Mac (clears memory pressure)
sudo reboot
```

**Quick Fix (Option 2 - Use smaller model):**
```python
# Edit mlx_medgemma_pipeline.py line 20
model_name = "google/gemma-2-9b-it"  # 9B instead of 27B
```

**Quick Fix (Option 3 - Increase swap):**
```bash
# Check current swap
sysctl vm.swapusage

# macOS automatically manages swap, but ensure you have 50GB+ free disk
df -h ~
```

**Root Cause:** 27B model needs ~16GB RAM. If system has other apps running, it exceeds available memory.

---

### Issue 3: Model download stuck or very slow

**Symptom:**
```
Downloading model-00001-of-00005.safetensors: 0%|          | 0/5.0G [00:00<?, ?B/s]
```

**Quick Fix (Option 1 - Check network):**
```bash
# Test HuggingFace connection
curl -I https://huggingface.co
# Should return: HTTP/2 200

# If slow/blocked, use mirror:
export HF_ENDPOINT="https://hf-mirror.com"
# Then re-run Python script
```

**Quick Fix (Option 2 - Resume download):**
```bash
# HuggingFace automatically resumes. Just restart script:
python mlx_medgemma_pipeline.py
```

**Quick Fix (Option 3 - Manual download):**
```bash
# Download via browser (faster with download manager):
# https://huggingface.co/google/gemma-2-27b-it/tree/main

# Place in cache:
mkdir -p ~/.cache/huggingface/hub
# Then move downloaded files there
```

**Root Cause:** Large model files (3-5GB each), slow internet, or HuggingFace server overload.

---

### Issue 4: Inference very slow (< 10 tokens/sec)

**Symptom:**
```
Tokens/sec: 5-8 (should be 40-50 on M4 Max)
```

**Quick Fix (Option 1 - Check GPU usage):**
```bash
# Open Activity Monitor
# Window → GPU History

# Should see 60-80% GPU usage during inference
# If 0%, MLX isn't using GPU
```

**Quick Fix (Option 2 - Verify MLX device):**
```python
python3 -c "import mlx.core as mx; print(mx.default_device())"
# Should output: Device(gpu, 0)
# If shows 'cpu', reinstall MLX
```

**Quick Fix (Option 3 - Reinstall MLX):**
```bash
pip uninstall mlx mlx-lm
pip cache purge
pip install mlx-lm --no-cache-dir
```

**Quick Fix (Option 4 - Close background apps):**
```bash
# Other apps may be hogging GPU
# Check Activity Monitor → GPU tab
# Close heavy apps (Chrome with many tabs, Final Cut, etc.)
```

**Root Cause:** MLX not using GPU, or GPU contention with other apps.

---

### Issue 5: "ModuleNotFoundError: No module named 'fhir'"

**Symptom:**
```python
ModuleNotFoundError: No module named 'fhir'
```

**Quick Fix:**
```bash
pip install fhir.resources
```

**Verify:**
```python
python3 -c "from fhir.resources import medicationstatement; print('OK')"
```

**Root Cause:** FHIR library not installed.

---

### Issue 6: Django "ModuleNotFoundError: No module named 'mlx_views'"

**Symptom:**
```
ModuleNotFoundError: No module named 'med_app.mlx_views'
```

**Quick Fix:**
```bash
# Verify file exists
ls -la med_app/mlx_views.py
# Should show the file

# If missing, it wasn't created. Check current directory:
pwd
# Should be: /Users/chiragkular/Documents/Dev/ck4957_Repos/med-parser

# Restart Django
python manage.py runserver
```

**Root Cause:** File not in expected location, or Django didn't reload.

---

### Issue 7: API returns 503 "Pipeline not available"

**Symptom:**
```json
{
  "success": false,
  "error": "MLX pipeline not available. Check server logs."
}
```

**Quick Fix:**
```bash
# Check Django terminal for detailed errors
# Common causes:

# 1. MLX not installed
pip install mlx-lm

# 2. FHIR not installed
pip install fhir.resources

# 3. Model not downloaded yet
# Solution: Wait 30-60s for first request to complete model loading
# Subsequent requests will be instant

# 4. Import error
# Check Django logs for actual error message
```

**Root Cause:** First API call triggers model loading (slow). Or missing dependencies.

---

### Issue 8: "CSRF verification failed" on API calls

**Symptom:**
```
Forbidden (CSRF token missing or incorrect)
```

**Quick Fix (Development only):**

Already handled in `mlx_views.py` with:
```python
@csrf_exempt
```

If still seeing error:
```bash
# Verify you're POSTing to correct endpoint:
curl -X POST http://localhost:8000/api/process-medical-text/ \
  -H "Content-Type: application/json" \
  -d '{"transcript": "test"}'

# Note: Must include Content-Type header
```

**Root Cause:** CSRF protection (normal Django behavior). Already disabled for demo.

---

### Issue 9: "Could not extract valid JSON from response"

**Symptom:**
```
⚠️  Could not extract valid JSON from response
```

**Quick Fix (Option 1 - Check model output):**

Add debug logging:
```python
# In mlx_medgemma_pipeline.py, line ~175
logger.debug(f"Raw response: {raw_response}")
```

**Quick Fix (Option 2 - Retry with lower temperature):**
```python
pipeline = MedGemmaPipeline(
    temperature=0.0  # Maximum determinism
)
```

**Quick Fix (Option 3 - Use more specific prompt):**

Edit `create_medical_prompt()` to be more explicit:
```python
"Output MUST be valid JSON. Start with { and end with }. No markdown."
```

**Root Cause:** Model occasionally outputs markdown-wrapped JSON or adds explanatory text.

---

### Issue 10: Model outputs invalid medical codes

**Symptom:**
```
⚠️  Invalid ICD-10 code for 'Diabetes'
⚠️  Invalid RxNorm code for 'Aspirin'
```

**This is expected!** The three-layer validation handles this:

1. ✅ First layer catches it (FHIR validation)
2. ✅ Second layer tries self-correction
3. ✅ Third layer uses vector DB fallback

**If still failing:**
```python
# Add more codes to vector DB
# Edit mlx_advanced_pipeline.py, line ~60:

def _load_icd10_codes(self):
    return {
        "I10": "Essential hypertension",
        "E11.9": "Type 2 diabetes",
        # Add your codes here:
        "E11.65": "Type 2 diabetes with hyperglycemia",
        "I25.10": "Coronary artery disease",
        # ... etc
    }
```

**Root Cause:** Model hallucinating codes not in vector DB. Solution: Expand the database.

---

## 🔍 General Debugging Strategy

### Step 1: Identify the Layer

```
Is error in:
├── Environment Setup?     → Python version, MLX install
├── Model Loading?         → Memory, disk space, network
├── Inference?             → GPU usage, MLX device
├── Validation?            → FHIR library, code databases
└── API Integration?       → Django settings, endpoints
```

### Step 2: Check Logs

```bash
# Python script logs
python mlx_advanced_pipeline.py 2>&1 | tee debug.log

# Django logs
python manage.py runserver 2>&1 | tee django_debug.log

# System logs
log show --predicate 'process == "Python"' --last 5m
```

### Step 3: Verify Environment

```bash
# Run comprehensive check
python test_mlx_setup.py > setup_report.txt

# Check Python packages
pip list | grep -E "mlx|fhir|django"

# Check Python path
python3 -c "import sys; print('\n'.join(sys.path))"
```

### Step 4: Isolate the Issue

```python
# Test MLX independently
from mlx_lm import load
model, tokenizer = load("google/gemma-2-9b-it")  # Smaller model
print("MLX works!")

# Test FHIR independently
from fhir.resources import medicationstatement
print("FHIR works!")

# Test Django independently
python manage.py check
python manage.py runserver --verbosity 3
```

---

## 🩺 Health Check Command

**Run this to diagnose issues:**

```bash
#!/bin/bash
echo "=== MLX HEALTH CHECK ==="
echo ""

echo "1. Architecture:"
uname -m

echo ""
echo "2. Python version:"
python3 --version

echo ""
echo "3. MLX installed:"
python3 -c "import mlx; print('YES:', mlx.__version__)" 2>&1

echo ""
echo "4. MLX-LM installed:"
python3 -c "from mlx_lm import load; print('YES')" 2>&1

echo ""
echo "5. FHIR installed:"
python3 -c "from fhir.resources import medicationstatement; print('YES')" 2>&1

echo ""
echo "6. MLX device:"
python3 -c "import mlx.core as mx; print(mx.default_device())" 2>&1

echo ""
echo "7. Available memory:"
python3 -c "import psutil; print(f'{psutil.virtual_memory().available / 1e9:.1f} GB')" 2>&1

echo ""
echo "8. Free disk space:"
df -h ~ | tail -n 1

echo ""
echo "9. HuggingFace reachable:"
curl -I -s https://huggingface.co | head -n 1

echo ""
echo "10. Files present:"
ls -l mlx_medgemma_pipeline.py mlx_advanced_pipeline.py med_app/mlx_views.py 2>&1

echo ""
echo "=== END HEALTH CHECK ==="
```

**Save as `health_check.sh` and run:**
```bash
chmod +x health_check.sh
./health_check.sh
```

---

## 📞 Getting Help

### If still stuck after trying above:

1. **Check GitHub Issues:**
   - MLX: https://github.com/ml-explore/mlx/issues
   - MedGemma: https://huggingface.co/google/gemma-2-27b-it/discussions

2. **Community Resources:**
   - MLX Discord: https://discord.gg/mlx
   - FHIR Python: https://github.com/nazrulworld/fhir.resources/issues

3. **Create Debug Report:**
```bash
# Run health check
./health_check.sh > debug_report.txt

# Add error logs
python mlx_advanced_pipeline.py 2>&1 >> debug_report.txt

# Share debug_report.txt when asking for help
```

---

## ✅ Quick Verification After Fixes

```bash
# 1. System check
python test_mlx_setup.py
# Should show: ✅ ALL CHECKS PASSED!

# 2. Pipeline test
python mlx_medgemma_pipeline.py
# Should complete without errors

# 3. API test
python manage.py runserver &
sleep 5
curl http://localhost:8000/api/health/
# Should return: {"status": "healthy"}

# Clean up
pkill -f "manage.py runserver"
```

---

## 🎯 Pro Tips

**Tip 1:** Always work in a virtual environment
```bash
python3 -m venv venv_mlx
source venv_mlx/bin/activate
```

**Tip 2:** Keep a "known good" terminal tab
```bash
# Terminal 1: Working environment
source venv_mlx/bin/activate
python mlx_advanced_pipeline.py

# Terminal 2: Experiments
# Try fixes here without affecting working env
```

**Tip 3:** Use verbose mode for debugging
```python
# In mlx_medgemma_pipeline.py
response = generate(
    model,
    tokenizer,
    prompt=prompt,
    max_tokens=self.max_tokens,
    temp=self.temperature,
    verbose=True  # Shows token generation
)
```

**Tip 4:** Monitor resources during debugging
```bash
# Terminal 1: Your script
python mlx_advanced_pipeline.py

# Terminal 2: Resource monitor
watch -n 1 'echo "Memory:" && free -h && echo "" && echo "GPU:" && nvidia-smi'
# (On Mac, use Activity Monitor instead)
```

---

## 🚀 Emergency Demo Recovery

**If demo crashes during presentation:**

### Plan A: Switch to Basic Pipeline
```bash
# Instead of advanced, run basic:
python mlx_medgemma_pipeline.py
```

### Plan B: Show Pre-Recorded Output
```bash
# Have a sample output saved:
python mlx_advanced_pipeline.py > sample_output.txt
# Then just: cat sample_output.txt
```

### Plan C: Walk Through Code
```bash
# Open the Python file in VS Code
# Explain the architecture without running
code mlx_advanced_pipeline.py
```

### Plan D: Show Documentation
```bash
# Open architecture diagram
open ARCHITECTURE.md
# Explain the design
```

**Remember:** Even if the demo fails, the code and docs prove your work!

---

**Keep this file bookmarked. You'll need it!** 🔖
