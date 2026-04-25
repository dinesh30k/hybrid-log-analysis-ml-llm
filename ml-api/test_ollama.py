#!/usr/bin/env python3
"""
Test script for Ollama integration
Run this after starting the API: python test_ollama.py
"""

import requests
import json
import time
from typing import Dict, Any

API_BASE = "http://127.0.0.1:8000"

def print_result(title: str, result: Dict[Any, Any], color: str = ""):
    """Pretty print results"""
    print(f"\n{'='*60}")
    print(f"✅ {title}")
    print(f"{'='*60}")
    print(json.dumps(result, indent=2))

def test_ollama_status():
    """Test 1: Check if Ollama is available"""
    print("\n🧪 Test 1: Ollama Status Check")
    try:
        response = requests.get(f"{API_BASE}/ollama/status", timeout=60)
        result = response.json()
        print_result("Ollama Status", result)
        
        if result.get("ollama_available"):
            print("✅ Ollama is running and ready!")
            return True
        else:
            print("❌ Ollama is not available. Make sure to run: ollama serve")
            return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_predict_low_confidence():
    """Test 2: Test hybrid prediction with low confidence fallback"""
    print("\n🧪 Test 2: Hybrid Prediction (Low Confidence → Ollama Fallback)")
    
    log = "unusual-error-not-in-training-data-pattern"
    
    try:
        response = requests.post(
            f"{API_BASE}/predict",
            json={"log": log, "use_ollama": False},
            timeout=60
        )
        result = response.json()
        print_result("Prediction Result", result)
        
        if result.get("prediction_source") == "ollama_analysis":
            print("✅ Successfully fell back to Ollama for low confidence!")
        
        return True
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_pure_ollama_analysis():
    """Test 3: Pure Ollama analysis"""
    print("\n🧪 Test 3: Pure Ollama Analysis")
    
    log = "Disk failure on DataNode 10.250.122.127: volume unwritable"
    
    try:
        response = requests.post(
            f"{API_BASE}/ollama/analyze",
            json={"log": log, "detailed": True},
            timeout=60
        )
        result = response.json()
        print_result("Ollama Analysis", result)
        return True
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_ml_prediction():
    """Test 4: Standard ML model prediction"""
    print("\n🧪 Test 4: ML Model Prediction (Standard)")
    
    log = "SSL handshake failure with 10.251.150.44: certificate not trusted"
    
    try:
        response = requests.post(
            f"{API_BASE}/predict",
            json={"log": log, "use_ollama": False},
            timeout=60
        )
        result = response.json()
        print_result("ML Prediction", result)
        return True
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_compare_predictions():
    """Test 5: Compare ML vs Ollama predictions"""
    print("\n🧪 Test 5: Compare ML vs Ollama Predictions")
    
    log = "Failed to replicate block: No live DataNodes available"
    
    try:
        response = requests.post(
            f"{API_BASE}/ollama/compare",
            json={"log": log},
            timeout=60
        )
        result = response.json()
        print_result("ML vs Ollama Comparison", result)
        
        ml_pred = result.get("ml_prediction", {}).get("severity")
        ollama_pred = result.get("ollama_prediction", {}).get("severity")
        
        if ml_pred and ollama_pred:
            print(f"\n📊 Comparison:")
            print(f"   ML Model: {ml_pred}")
            print(f"   Ollama LLM: {ollama_pred}")
            
            if ml_pred != ollama_pred:
                print("   ⚠️  Predictions differ - use comparison to decide")
        
        return True
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_ollama_summary():
    """Test 6: Get Ollama system summary"""
    print("\n🧪 Test 6: Ollama System Summary (AI Analysis)")
    
    try:
        response = requests.get(
            f"{API_BASE}/ollama/summary",
            timeout=60
        )
        result = response.json()
        print_result("System Summary", result)
        return True
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║     🤖 Ollama Integration Test Suite                    ║
    ║     Testing ML + Ollama Hybrid System                   ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    # Check API is running
    print("🔍 Checking if API is running...")
    try:
        response = requests.get(f"{API_BASE}/logs", timeout=60)
        print("✓ API is running!")
    except:
        print("❌ API is not running!")
        print("Start it with: uvicorn app:app --reload")
        return
    
    print("\n" + "="*60)
    print("Starting tests... (This may take 1-2 minutes)")
    print("="*60)
    
    tests = [
        ("Ollama Status", test_ollama_status),
        ("ML Prediction", test_ml_prediction),
        ("Low Confidence Fallback", test_predict_low_confidence),
        ("Pure Ollama Analysis", test_pure_ollama_analysis),
        ("ML vs Ollama Comparison", test_compare_predictions),
        ("Ollama Summary", test_ollama_summary),
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            success = test_func()
            results[name] = "✅ PASS" if success else "❌ FAIL"
        except Exception as e:
            print(f"❌ Test failed with error: {str(e)}")
            results[name] = "❌ ERROR"
        
        time.sleep(1)  # Small delay between tests
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    for test_name, result in results.items():
        print(f"{result} - {test_name}")
    
    passed = sum(1 for r in results.values() if "PASS" in r)
    total = len(results)
    
    print(f"\n🎯 Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ All tests passed! System is ready for production!")
    else:
        print("\n⚠️  Some tests failed. Check the output above.")

if __name__ == "__main__":
    main()
