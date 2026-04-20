import json
import os

def validate_lab():
    print("Checking submission format...")
    
    required_files = [
        "reports/summary.json",
        "reports/benchmark_results.json",
        "analysis/failure_analysis.md"
    ]
    
    # 1. Check file existence
    for f in required_files:
        if os.path.exists(f):
            print(f"Passed: Found {f}")
        else:
            print(f"Failed: Missing file {f}")
            return

    # 2. Check summary.json content
    with open("reports/summary.json", "r") as f:
        data = json.load(f)
        
        metrics = data["metrics"]
        
        print(f"\n--- Quick Stats ---")
        total_key = "total_cases" if "total_cases" in data["metadata"] else "total"
        print(f"Total cases: {data['metadata'][total_key]}")
        print(f"Average Score: {metrics['avg_score']:.2f}")
        
        # EXPERT CHECKS
        has_retrieval = "hit_rate" in metrics
        has_multi_judge = "agreement_rate" in metrics or "avg_score" in metrics
        
        if has_retrieval:
            print(f"Passed: Retrieval Metrics found (Hit Rate: {metrics['hit_rate']*100:.1f}%)")
        else:
            print(f"Warning: Missing Retrieval Metrics.")

        if data["metadata"].get("version"):
            print(f"Passed: Agent Version info found (Regression Mode)")

    print("\nResult: Lab is ready for grading!")

if __name__ == "__main__":
    validate_lab()
