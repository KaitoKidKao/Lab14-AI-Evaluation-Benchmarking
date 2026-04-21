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
            
            # 1. Xử lý input (question hoặc messages)
            messages = test_case.get("messages")
            question = test_case.get("question")
            
            if messages:
                response = await self.agent.query(messages=messages, **kwargs)
                query_text = messages[-1]["content"]
                history = messages[:-1]
            else:
                response = await self.agent.query(question=question, **kwargs)
                query_text = question
                history = None

            latency = time.perf_counter() - start_time
            
            # 2. Chạy Retrieval Eval
            retrieved_ids = response.get("metadata", {}).get("sources", [])
            
            # 3. Chạy Multi-Judge
            judge_result = await self.judge.evaluate_multi_judge(
                query_text, 
                response["answer"], 
                test_case.get("expected_answer", ""),
                history=history
            )
            
            # Tính toán chi phí
            tokens = response.get("metadata", {}).get("tokens_used", 0)
            cost = (tokens / 1000) * self.cost_per_1k_tokens

            # Mock Ragas cho đồng bộ với báo cáo sample
            # (Trong môi trường production, bạn sẽ gọi lib ragas thật ở đây)
            ragas_metrics = {
                "hit_rate": 1.0 if any(id in retrieved_ids for id in test_case.get("expected_retrieval_ids", [])) else 0.0,
                "mrr": self.evaluator.calculate_mrr(test_case.get("expected_retrieval_ids", []), retrieved_ids),
                "faithfulness": 0.9 if judge_result["final_score"] >= 4 else 0.5,
                "relevancy": 0.8 if judge_result["final_score"] >= 3 else 0.4
            }

            return {
                "test_case": query_text,
                "expected_retrieval_ids": test_case.get("expected_retrieval_ids", []),
                "retrieved_ids": retrieved_ids,
                "agent_response": response["answer"],
                "latency": latency,
                "tokens": tokens,
                "cost": cost,
                "ragas": ragas_metrics,
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
