import asyncio
import json
import os
import time
from engine.runner import BenchmarkRunner
from agent.main_agent import MainAgent
from engine.retrieval_eval import RetrievalEvaluator
from engine.llm_judge import LLMJudge

async def run_benchmark_with_results(agent, agent_version: str):
    print(f"Starting Benchmark for {agent_version}...")
    
    if not os.path.exists("data/golden_set.jsonl"):
        print("Error: Missing data/golden_set.jsonl. Please run data/synthetic_gen.py first.")
        return None, None

    with open("data/golden_set.jsonl", "r", encoding="utf-8") as f:
        dataset = [json.loads(line) for line in f]

    evaluator = RetrievalEvaluator()
    judge = LLMJudge()
    runner = BenchmarkRunner(agent, evaluator, judge)
    
    results = await runner.run_all(dataset)
    retrieval_metrics = await evaluator.evaluate_batch(results)
    
    summary = {
        "metadata": {
            "version": agent_version, 
            "total_cases": len(results), 
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        },
        "metrics": {
            "avg_score": sum(r["judge"]["final_score"] for r in results) / len(results),
            "hit_rate": retrieval_metrics["avg_hit_rate"],
            "mrr": retrieval_metrics["avg_mrr"],
            "agreement_rate": sum(r["judge"]["agreement_rate"] for r in results) / len(results),
            "avg_latency": sum(r["latency"] for r in results) / len(results),
            "total_cost": sum(r["cost"] for r in results)
        }
    }
    return results, summary

async def main():
    agent = MainAgent()
    
    # 1. Chạy V1 Baseline (Mô phỏng bằng cách chạy lần đầu)
    print("--- PHASE 1: V1 BASELINE ---")
    v1_results, v1_summary = await run_benchmark_with_results(agent, "Agent_V1_Base")
    
    # 2. Chạy V2 Optimized (Trong lab này chúng ta dùng cùng agent nhưng mô phỏng sự khác biệt)
    print("\n--- PHASE 2: V2 OPTIMIZED ---")
    v2_results, v2_summary = await run_benchmark_with_results(agent, "Agent_V2_Optimized")
    
    if v1_summary and v2_summary:
        print("\n--- REGRESSION ANALYSIS RESULTS ---")
        score_v1 = v1_summary["metrics"]["avg_score"]
        score_v2 = v2_summary["metrics"]["avg_score"]
        delta = score_v2 - score_v1
        
        print(f"V1 Score: {score_v1:.2f}")
        print(f"V2 Score: {score_v2:.2f}")
        print(f"Delta: {'+' if delta >= 0 else ''}{delta:.2f}")
        print(f"Hit Rate: {v2_summary['metrics']['hit_rate']:.2%}")
        print(f"Agreement Rate: {v2_summary['metrics']['agreement_rate']:.2%}")
        print(f"Total Cost: ${v2_summary['metrics']['total_cost']:.4f}")
        
        # Lưu kết quả để nộp bài
        os.makedirs("reports", exist_ok=True)
        with open("reports/summary.json", "w", encoding="utf-8") as f:
            json.dump(v2_summary, f, ensure_ascii=False, indent=2)
        with open("reports/benchmark_results.json", "w", encoding="utf-8") as f:
            json.dump(v2_results, f, ensure_ascii=False, indent=2)

        # Logic Release Gate
        if delta >= 0 and v2_summary["metrics"]["hit_rate"] >= 0.8:
            print("\nDECISION: APPROVE RELEASE")
        else:
            print("\nDECISION: BLOCK RELEASE - Reason: Score decreased or Hit Rate too low")
            
    print("\nNext step: Run 'python check_lab.py' to verify formatting.")

if __name__ == "__main__":
    asyncio.run(main())
