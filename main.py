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

    # 2. Chạy V2 Optimized - Sử dụng Prompt được tối ưu hóa
    v2_optimized_prompt = """
    Bạn là chuyên gia tư vấn cao cấp của SmartBank. 
    Hãy trả lời dựa trên tài liệu sau:
    {{context}}
    
    YÊU CẦU QUAN TRỌNG:
    1. Trình bày bằng các gạch đầu dòng (bullet points) để khách hàng dễ đọc.
    2. Luôn bắt buộc trích dẫn Mã tài liệu (ví dụ: [ID tài liệu: DOC_REG_001]) ở cuối mỗi ý nếu thông tin lấy từ đó.
    3. Trả lời ngắn gọn, súc tích và chuyên nghiệp.
    4. Nếu câu hỏi liên quan đến nội dung ghi chú [HẾT HIỆU LỰC], hãy lịch sự từ chối và hướng dẫn khách hàng xem quy chuẩn mới.
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

        # HÀNH ĐỘNG: Show kết quả so sánh mẫu
        print("\n" + "="*50)
        print("🔍 SAMPLE COMPARISON (V1 vs V2)")
        print("="*50)
        sample_q = v1_results[0]['question']
        print(f"QUESTION: {sample_q}")
        print("-" * 30)
        print(f"🔴 V1 ANSWER (Baseline):\n{v1_results[0]['agent_response']}")
        print("-" * 30)
        print(f"🟢 V2 ANSWER (Optimized):\n{v2_results[0]['agent_response']}")
        print("="*50)

        # Logic Release Gate
        if delta >= 0 and v2_summary["metrics"]["hit_rate"] >= 0.8:
            print("\nDECISION: APPROVE RELEASE")
        else:
            print("\nDECISION: BLOCK RELEASE - Reason: Score decreased or Hit Rate too low")
            
    print("\nNext step: Run 'python check_lab.py' to verify formatting.")

if __name__ == "__main__":
    asyncio.run(main())
