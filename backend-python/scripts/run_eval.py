#!/usr/bin/env python3
"""
ComplaintOps Copilot - Mini Evaluation Script
Runs golden set through the pipeline and calculates metrics.

Usage:
    python scripts/run_eval.py [--java-url URL] [--python-url URL]
"""

import argparse
import json
import time
import sys
from pathlib import Path
from typing import Any

try:
    import requests
except ImportError:
    print("Please install requests: pip install requests")
    sys.exit(1)


def load_golden_set(path: str = "data/golden_set.json") -> dict:
    """Load the golden set from JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_pii_masking(python_url: str, text: str) -> dict:
    """Test PII masking endpoint."""
    try:
        resp = requests.post(
            f"{python_url}/mask",
            json={"text": text},
            headers={"X-Request-ID": f"eval-mask-{time.time()}"},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


def test_triage(python_url: str, text: str) -> dict:
    """Test triage endpoint."""
    try:
        resp = requests.post(
            f"{python_url}/predict",
            json={"text": text},
            headers={"X-Request-ID": f"eval-triage-{time.time()}"},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


def test_full_pipeline(java_url: str, text: str) -> tuple[dict, float]:
    """Test full pipeline through Java API."""
    try:
        start = time.time()
        resp = requests.post(
            f"{java_url}/api/sikayet",
            json={"metin": text},
            timeout=30,
        )
        latency = time.time() - start
        resp.raise_for_status()
        return resp.json(), latency
    except Exception as e:
        return {"error": str(e)}, 0.0


def map_category_to_english(turkish_category: str) -> str:
    """Map Turkish category back to English for comparison."""
    mapping = {
        "DOLANDIRICILIK_YETKISIZ_ISLEM": "FRAUD_UNAUTHORIZED_TX",
        "IADE_ITIRAZ": "CHARGEBACK_DISPUTE",
        "TRANSFER_GECIKMESI": "TRANSFER_DELAY",
        "ERISIM_GIRIS_MOBIL": "ACCESS_LOGIN_MOBILE",
        "KART_LIMIT_KREDI": "CARD_LIMIT_CREDIT",
        "BILGI_TALEBI": "INFORMATION_REQUEST",
        "KAMPANYA_PUAN_ODUL": "CAMPAIGN_POINTS_REWARDS",
        "MANUEL_INCELEME": "MANUAL_REVIEW",
    }
    return mapping.get(turkish_category, turkish_category)


def map_urgency_to_english(turkish_urgency: str) -> str:
    """Map Turkish urgency back to English for comparison."""
    mapping = {
        "YUKSEK": "HIGH",
        "ORTA": "MEDIUM",
        "DUSUK": "LOW",
    }
    return mapping.get(turkish_urgency, turkish_urgency)


def run_evaluation(
    golden_set: dict,
    java_url: str = "http://localhost:8080",
    python_url: str = "http://localhost:8000",
) -> dict:
    """Run full evaluation and return metrics."""
    
    results = {
        "total": len(golden_set["examples"]),
        "category_correct": 0,
        "urgency_correct": 0,
        "pii_leaked": 0,
        "pii_masked_correctly": 0,
        "errors": 0,
        "latencies": [],
        "details": [],
    }
    
    print(f"\n{'='*60}")
    print(f"ComplaintOps Copilot - Evaluation Run")
    print(f"Golden Set: {results['total']} examples")
    print(f"Java URL: {java_url}")
    print(f"Python URL: {python_url}")
    print(f"{'='*60}\n")
    
    for example in golden_set["examples"]:
        print(f"[{example['id']:02d}] Testing: {example['text'][:50]}...")
        
        detail = {
            "id": example["id"],
            "text": example["text"],
            "expected_category": example["expected_category"],
            "expected_urgency": example["expected_urgency"],
        }
        
        # Test PII masking first
        if example.get("pii_present"):
            mask_result = test_pii_masking(python_url, example["text"])
            if "error" not in mask_result:
                masked_text = mask_result.get("masked_text", "")
                # Check if any PII leaked
                pii_leaked = False
                for pii_type in example.get("pii_types", []):
                    # Simple check: look for patterns
                    if pii_type == "TCKN" and "12345678901" in masked_text:
                        pii_leaked = True
                    elif pii_type == "TR_IBAN" and "TR330006100519786457841326" in masked_text:
                        pii_leaked = True
                    elif pii_type == "EMAIL_ADDRESS" and "test@email.com" in masked_text:
                        pii_leaked = True
                    elif pii_type == "PHONE_NUMBER" and "05551234567" in masked_text:
                        pii_leaked = True
                
                if pii_leaked:
                    results["pii_leaked"] += 1
                    detail["pii_status"] = "LEAKED"
                else:
                    results["pii_masked_correctly"] += 1
                    detail["pii_status"] = "MASKED"
            else:
                detail["pii_status"] = "ERROR"
        
        # Test full pipeline
        response, latency = test_full_pipeline(java_url, example["text"])
        
        if "error" in response:
            results["errors"] += 1
            detail["status"] = "ERROR"
            detail["error"] = response["error"]
            print(f"     ❌ Error: {response['error'][:50]}")
        else:
            results["latencies"].append(latency)
            detail["latency_ms"] = round(latency * 1000, 2)
            detail["response"] = response
            
            # Check category
            predicted_category = map_category_to_english(response.get("kategori", ""))
            if predicted_category == example["expected_category"]:
                results["category_correct"] += 1
                detail["category_match"] = True
                cat_status = "✓"
            else:
                detail["category_match"] = False
                cat_status = "✗"
            
            # Check urgency
            predicted_urgency = map_urgency_to_english(response.get("oncelik", ""))
            if predicted_urgency == example["expected_urgency"]:
                results["urgency_correct"] += 1
                detail["urgency_match"] = True
                urg_status = "✓"
            else:
                detail["urgency_match"] = False
                urg_status = "✗"
            
            print(f"     Category: {cat_status} ({predicted_category}) | "
                  f"Urgency: {urg_status} ({predicted_urgency}) | "
                  f"Latency: {latency*1000:.0f}ms")
        
        results["details"].append(detail)
    
    # Calculate metrics
    successful = results["total"] - results["errors"]
    if successful > 0:
        results["category_accuracy"] = round(results["category_correct"] / successful * 100, 2)
        results["urgency_accuracy"] = round(results["urgency_correct"] / successful * 100, 2)
    else:
        results["category_accuracy"] = 0
        results["urgency_accuracy"] = 0
    
    pii_examples = sum(1 for e in golden_set["examples"] if e.get("pii_present"))
    if pii_examples > 0:
        results["pii_leak_rate"] = round(results["pii_leaked"] / pii_examples * 100, 2)
    else:
        results["pii_leak_rate"] = 0
    
    if results["latencies"]:
        results["latency_avg_ms"] = round(sum(results["latencies"]) / len(results["latencies"]) * 1000, 2)
        results["latency_p95_ms"] = round(sorted(results["latencies"])[int(len(results["latencies"]) * 0.95)] * 1000, 2)
    else:
        results["latency_avg_ms"] = 0
        results["latency_p95_ms"] = 0
    
    return results


def print_summary(results: dict) -> None:
    """Print evaluation summary."""
    print(f"\n{'='*60}")
    print("EVALUATION SUMMARY")
    print(f"{'='*60}")
    print(f"Total Examples:       {results['total']}")
    print(f"Successful:           {results['total'] - results['errors']}")
    print(f"Errors:               {results['errors']}")
    print(f"")
    print(f"Category Accuracy:    {results['category_accuracy']}%")
    print(f"Urgency Accuracy:     {results['urgency_accuracy']}%")
    print(f"PII Leak Rate:        {results['pii_leak_rate']}%")
    print(f"")
    print(f"Latency (avg):        {results['latency_avg_ms']}ms")
    print(f"Latency (p95):        {results['latency_p95_ms']}ms")
    print(f"{'='*60}")
    
    # Pass/Fail criteria
    print("\nPASS/FAIL CRITERIA:")
    passed = True
    
    if results["category_accuracy"] >= 70:
        print(f"  ✅ Category Accuracy >= 70%: PASS ({results['category_accuracy']}%)")
    else:
        print(f"  ❌ Category Accuracy >= 70%: FAIL ({results['category_accuracy']}%)")
        passed = False
    
    if results["pii_leak_rate"] == 0:
        print(f"  ✅ PII Leak Rate = 0%: PASS")
    else:
        print(f"  ❌ PII Leak Rate = 0%: FAIL ({results['pii_leak_rate']}%)")
        passed = False
    
    if results["latency_p95_ms"] <= 5000:
        print(f"  ✅ Latency p95 <= 5s: PASS ({results['latency_p95_ms']}ms)")
    else:
        print(f"  ❌ Latency p95 <= 5s: FAIL ({results['latency_p95_ms']}ms)")
        passed = False
    
    print(f"\nOVERALL: {'✅ PASS' if passed else '❌ FAIL'}")


def main():
    parser = argparse.ArgumentParser(description="ComplaintOps Copilot Evaluation")
    parser.add_argument("--java-url", default="http://localhost:8080", help="Java backend URL")
    parser.add_argument("--python-url", default="http://localhost:8000", help="Python AI service URL")
    parser.add_argument("--golden-set", default="data/golden_set.json", help="Path to golden set JSON")
    parser.add_argument("--output", default=None, help="Output JSON file for results")
    args = parser.parse_args()
    
    # Load golden set
    try:
        golden_set = load_golden_set(args.golden_set)
    except FileNotFoundError:
        print(f"Error: Golden set not found at {args.golden_set}")
        sys.exit(1)
    
    # Run evaluation
    results = run_evaluation(golden_set, args.java_url, args.python_url)
    
    # Print summary
    print_summary(results)
    
    # Save results if requested
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\nResults saved to: {args.output}")


if __name__ == "__main__":
    main()
