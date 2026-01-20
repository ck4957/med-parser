#!/usr/bin/env python3
"""
Quick test script to verify MLX setup before running full pipeline.
Run this BEFORE the main pipeline to catch issues early.
"""

import sys
import os

def test_python_version():
    """Verify Python version"""
    print("🔍 Checking Python version...")
    if sys.version_info < (3, 9):
        print(f"   ❌ Python {sys.version_info.major}.{sys.version_info.minor} detected")
        print(f"   ⚠️  Recommended: Python 3.9+")
        return False
    print(f"   ✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True

def test_architecture():
    """Verify running on Apple Silicon"""
    print("\n🔍 Checking architecture...")
    import platform
    arch = platform.machine()
    
    if arch != "arm64":
        print(f"   ❌ Architecture: {arch}")
        print(f"   ⚠️  MLX requires Apple Silicon (arm64)")
        print(f"   💡 You're on Intel/AMD. Consider using Ollama instead.")
        return False
    
    print(f"   ✅ Architecture: {arch} (Apple Silicon)")
    return True

def test_mlx_installation():
    """Verify MLX is installed and working"""
    print("\n🔍 Checking MLX installation...")
    
    try:
        import mlx
        print(f"   ✅ MLX installed (version {mlx.__version__})")
        return True
    except ImportError:
        print(f"   ❌ MLX not installed")
        print(f"   💡 Run: pip install mlx-lm")
        return False

def test_mlx_lm_installation():
    """Verify MLX LM is installed"""
    print("\n🔍 Checking MLX-LM installation...")
    
    try:
        from mlx_lm import load, generate
        print(f"   ✅ MLX-LM installed")
        return True
    except ImportError:
        print(f"   ❌ MLX-LM not installed")
        print(f"   💡 Run: pip install mlx-lm")
        return False

def test_fhir_installation():
    """Verify FHIR library is installed"""
    print("\n🔍 Checking FHIR library...")
    
    try:
        from fhir.resources.medicationstatement import MedicationStatement
        print(f"   ✅ FHIR library installed")
        return True
    except ImportError:
        print(f"   ⚠️  FHIR library not installed (optional)")
        print(f"   💡 Run: pip install fhir.resources")
        return False

def test_disk_space():
    """Check available disk space"""
    print("\n🔍 Checking disk space...")
    
    try:
        import shutil
        home = os.path.expanduser("~")
        stats = shutil.disk_usage(home)
        
        free_gb = stats.free / (1024**3)
        
        if free_gb < 15:
            print(f"   ⚠️  Free space: {free_gb:.1f} GB")
            print(f"   ⚠️  Recommended: 15GB+ for model download")
            return False
        
        print(f"   ✅ Free space: {free_gb:.1f} GB")
        return True
    
    except Exception as e:
        print(f"   ⚠️  Could not check disk space: {e}")
        return True

def test_huggingface_cache():
    """Check HuggingFace cache directory"""
    print("\n🔍 Checking HuggingFace cache...")
    
    cache_dir = os.path.expanduser("~/.cache/huggingface")
    
    if os.path.exists(cache_dir):
        print(f"   ✅ Cache directory exists: {cache_dir}")
        
        # Check if model already downloaded
        model_cache = os.path.join(cache_dir, "hub")
        if os.path.exists(model_cache):
            model_dirs = [d for d in os.listdir(model_cache) if "gemma" in d.lower()]
            if model_dirs:
                print(f"   ℹ️  Found existing Gemma models: {len(model_dirs)}")
                return True
    else:
        print(f"   ℹ️  Cache directory will be created on first run")
    
    return True

def test_memory():
    """Estimate available memory"""
    print("\n🔍 Checking available memory...")
    
    try:
        import psutil
        mem = psutil.virtual_memory()
        
        total_gb = mem.total / (1024**3)
        available_gb = mem.available / (1024**3)
        
        print(f"   ℹ️  Total RAM: {total_gb:.1f} GB")
        print(f"   ℹ️  Available RAM: {available_gb:.1f} GB")
        
        if available_gb < 10:
            print(f"   ⚠️  Low memory. Close other apps before running.")
            print(f"   💡 Recommended: 16GB+ free for 27B 4-bit model")
            return False
        
        if total_gb >= 48:
            print(f"   ✅ Sufficient RAM for 27B model (4-bit)")
        elif total_gb >= 32:
            print(f"   ✅ Should work, but consider using 9B model if issues")
        else:
            print(f"   ⚠️  Consider using 9B model instead of 27B")
        
        return True
    
    except ImportError:
        print(f"   ⚠️  psutil not installed (optional check)")
        print(f"   💡 Run: pip install psutil")
        return True

def main():
    """Run all tests"""
    print("=" * 70)
    print("🧪 MLX PIPELINE PRE-FLIGHT CHECK")
    print("=" * 70)
    
    tests = [
        ("Python Version", test_python_version),
        ("Architecture", test_architecture),
        ("MLX Core", test_mlx_installation),
        ("MLX-LM", test_mlx_lm_installation),
        ("FHIR Library", test_fhir_installation),
        ("Disk Space", test_disk_space),
        ("HuggingFace Cache", test_huggingface_cache),
        ("Memory", test_memory),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"   ❌ Test failed with error: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}: {name}")
    
    print("\n" + "-" * 70)
    print(f"   Result: {passed}/{total} tests passed")
    print("-" * 70)
    
    if passed == total:
        print("\n✅ ALL CHECKS PASSED!")
        print("   You're ready to run: python mlx_medgemma_pipeline.py")
    elif passed >= total - 2:
        print("\n⚠️  MOST CHECKS PASSED")
        print("   You can try running the pipeline, but may encounter issues")
    else:
        print("\n❌ MULTIPLE CHECKS FAILED")
        print("   Fix the issues above before proceeding")
    
    print("\n💡 TROUBLESHOOTING:")
    print("   1. Ensure you're on Apple Silicon (M1/M2/M3/M4)")
    print("   2. Install dependencies: pip install -r requirements_mlx.txt")
    print("   3. Check MLX docs: https://github.com/ml-explore/mlx")
    print("=" * 70 + "\n")
    
    sys.exit(0 if passed == total else 1)

if __name__ == "__main__":
    main()
