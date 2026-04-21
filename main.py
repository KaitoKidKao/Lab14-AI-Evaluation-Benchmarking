import asyncio
import json
import os
import time
import sys
import io

# Ép Terminal sử dụng UTF-8 để hiển thị tiếng Việt chính xác trên Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

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
        print("❌ File data/golden_set.jsonl rỗng. Hãy tạo ít nhất 1 test case.")
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
    agent = MainAgent()
    
    # 1. Chạy V1 Baseline (Mô phỏng bằng cách chạy lần đầu)
    print("--- PHASE 1: V1 BASELINE ---")
    v1_results, v1_summary = await run_benchmark_with_results(agent, "Agent_V1_Base")
    
    # Đợi 1 chút để các kết nối async được đóng sạch sẽ trên Windows
    agent.langfuse.flush()
    await asyncio.sleep(1)

    v2_optimized_prompt = """
    Bạn là AI Assistant cao cấp của SmartBank. 
    Nhiệm vụ: Trả lời CHUYÊN NGHIỆP, CHÍNH XÁC và LUÔN TRÍCH DẪN NGUỒN.

    Dưới đây là tài liệu nghiệp vụ (Context):
    {{context}}
    
    YÊU CẦU THỰC THI:
    1. Trả lời trực tiếp vào vấn đề, sử dụng các gạch đầu dòng rõ ràng.
    2. Bắt buộc trích dẫn mã tài liệu ở cuối mỗi ý (ví dụ: [Nguồn: DOC_REG_001]).
    3. Nếu tài liệu bị đánh dấu [HẾT HIỆU LỰC], hãy từ chối lịch sự và dẫn hướng tới DOC_TRANS_003.

    VÍ DỤ:
    Câu hỏi: Hạn mức chuyển tiền là bao nhiêu?
    Trả lời: 
    - Hạn mức chuyển tiền mặc định của SmartBank là 50.000.000 VND/ngày. [Nguồn: DOC_TRANS_003]
    """
    
    print("\n--- PHASE 2: V2 OPTIMIZED ---")
    v2_results, v2_summary = await run_benchmark_with_results(
        agent, 
        "Agent_V2_Optimized", 
        prompt_override=v2_optimized_prompt
    )
    
    agent.langfuse.flush()
    
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
