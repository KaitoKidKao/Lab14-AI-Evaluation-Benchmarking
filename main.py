import asyncio
import json
import os
import time
from engine.runner import BenchmarkRunner
from agent.main_agent import MainAgent
from engine.retrieval_eval import RetrievalEvaluator
from engine.llm_judge import LLMJudge
from langfuse import observe

@observe()
async def run_benchmark_with_results(agent, agent_version: str, **kwargs):
    print(f"Starting Benchmark for {agent_version}...")
    
    if not os.path.exists("data/golden_set.jsonl"):
        print("Error: Missing data/golden_set.jsonl. Please run data/synthetic_gen.py first.")
        return None, None

    with open("data/golden_set.jsonl", "r", encoding="utf-8") as f:
        dataset = []
        for line in f:
            clean_line = line.strip()
            if not clean_line or clean_line.startswith("//"):
                continue
            try:
                dataset.append(json.loads(clean_line))
            except json.JSONDecodeError:
                continue

    if not dataset:
        print(" File data/golden_set.jsonl rỗng. Hãy tạo ít nhất 1 test case.")
        return None, None

    evaluator = RetrievalEvaluator()
    judge = LLMJudge()
    runner = BenchmarkRunner(agent, evaluator, judge)
    
    results = await runner.run_all(dataset, **kwargs)
    retrieval_metrics = await evaluator.evaluate_batch(results)
    
    total = len(results)

    summary = {
        "metadata": {
            "version": agent_version, 
            "total_cases": total, 
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        },
        "metrics": {
            "avg_score": sum(r["judge"]["final_score"] for r in results) / total,
            "hit_rate": retrieval_metrics["avg_hit_rate"],
            "mrr": retrieval_metrics["avg_mrr"],
            "agreement_rate": sum(r["judge"]["agreement_rate"] for r in results) / total,
            "avg_latency": sum(r["latency"] for r in results) / total,
            "total_cost": sum(r["cost"] for r in results)
        }
    }
    return results, summary

async def main():
    # 1. Chạy V1 Baseline (gpt-4o-mini)
    print("--- PHASE 1: V1 BASELINE (gpt-4o-mini) ---")
    agent_v1 = MainAgent(model_name="gpt-4o-mini")
    v1_results, v1_summary = await run_benchmark_with_results(agent_v1, "V1-Baseline")
    
    # 2. Chạy V2 Optimized (Bạn có thể đổi sang model khác như gpt-4o ở đây)
    print("\n--- PHASE 2: V2 OPTIMIZED (gpt-4o-mini) ---")
    agent_v2 = MainAgent(model_name="gpt-4o-mini")
    v2_results, v2_summary = await run_benchmark_with_results(agent_v2, "V2-Optimized")
    
    if v1_summary and v2_summary:
        from engine.release_gate import ReleaseGate
        
        print("\n--- REGRESSION ANALYSIS & AUTO-GATE ---")
        
        # Khởi tạo Gate với các ngưỡng cấu hình
        gate = ReleaseGate(
            min_hit_rate=0.8,
            max_latency_increase=0.2,
            max_cost=0.05
        )
        
        # Thực hiện đánh giá
        is_approved, gate_report = gate.evaluate_gate(v1_summary, v2_summary)
        
        # In báo cáo chi tiết
        print(gate_report)
        
        # Lưu kết quả để nộp bài
        os.makedirs("reports", exist_ok=True)
        with open("reports/summary.json", "w", encoding="utf-8") as f:
            # Bổ sung trạng thái release vào summary
            v2_summary["release_decision"] = "APPROVED" if is_approved else "BLOCKED"
            json.dump(v2_summary, f, ensure_ascii=False, indent=2)
        
        with open("reports/benchmark_results.json", "w", encoding="utf-8") as f:
            json.dump(v2_results, f, ensure_ascii=False, indent=2)
            
    print("\nNext step: Run 'python check_lab.py' to verify formatting.")

if __name__ == "__main__":
    asyncio.run(main())
