import asyncio
import time
from typing import List, Dict
from langfuse import observe

class BenchmarkRunner:
    def __init__(self, agent, evaluator, judge, concurrency: int = 5):
        self.agent = agent
        self.evaluator = evaluator
        self.judge = judge
        self.semaphore = asyncio.Semaphore(concurrency)
        self.cost_per_1k_tokens = 0.00015 # Giả lập giá gpt-4o-mini

    @observe()
    async def run_single_test(self, test_case: Dict, **kwargs) -> Dict:
        async with self.semaphore:
            start_time = time.perf_counter()
            
            # 1. Gọi Agent với các tham số tùy chỉnh (ví dụ: prompt_label, prompt_override)
            response = await self.agent.query(test_case["question"], **kwargs)
            latency = time.perf_counter() - start_time
            
            # 2. Chạy Retrieval Eval
            # Agent trả về 'contexts' và 'metadata', chúng ta mô phỏng retrieved_ids
            retrieved_ids = response.get("metadata", {}).get("sources", [])
            
            # 3. Chạy Multi-Judge
            judge_result = await self.judge.evaluate_multi_judge(
                test_case["question"], 
                response["answer"], 
                test_case["expected_answer"]
            )
            
            # Tính toán chi phí (giả lập)
            tokens = response.get("metadata", {}).get("tokens_used", 0)
            cost = (tokens / 1000) * self.cost_per_1k_tokens

            return {
                "question": test_case["question"],
                "expected_retrieval_ids": test_case.get("expected_retrieval_ids", []),
                "retrieved_ids": retrieved_ids,
                "agent_response": response["answer"],
                "latency": latency,
                "tokens": tokens,
                "cost": cost,
                "judge": judge_result,
                "status": "fail" if judge_result["final_score"] < 3 else "pass"
            }

    async def run_all(self, dataset: List[Dict], batch_size: int = 5, **kwargs) -> List[Dict]:
        """
        Chạy song song bằng asyncio.gather với giới hạn batch_size để không bị Rate Limit.
        """
        results = []
        for i in range(0, len(dataset), batch_size):
            batch = dataset[i:i + batch_size]
            tasks = [self.run_single_test(case, **kwargs) for case in batch]
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
        return results
