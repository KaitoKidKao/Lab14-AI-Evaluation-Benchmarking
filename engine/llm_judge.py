import os
import asyncio
import json
import re
import random
from typing import List, Dict, Any
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

class LLMJudge:
    """
    Hệ thống Multi-Judge để chấm điểm câu trả lời của Agent.
    Sử dụng gpt-4o-mini và gpt-3.5-turbo để thực hiện consensus.
    """
    def __init__(self, models: List[str] = ["gpt-4o-mini", "gpt-5-nano"]):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.models = models
        self.judges = [
            {"model": models[0], "temp": 0.0},
            {"model": models[1], "temp": 0.7}
        ]

    async def _get_judge_score(self, model: str, temp: float, question: str, answer: str, ground_truth: str) -> int:
        """
        Gọi API OpenAI để lấy điểm số từ một Judge.
        """
        prompt = f"""
        Bạn là một chuyên gia đánh giá chất lượng AI. Hãy chấm điểm câu trả lời của AI dựa trên Ground Truth (Sự thật hiển nhiên).
        
        Câu hỏi: {question}
        Câu trả lời của AI: {answer}
        Ground Truth: {ground_truth}
        
        Tiêu chí chấm điểm:
        - 5 điểm: Hoàn hảo, đầy đủ ý, chính xác 100%.
        - 4 điểm: Chính xác nhưng có thể diễn đạt tốt hơn hoặc thiếu một ý nhỏ không quan trọng.
        - 3 điểm: Đúng ý chính nhưng trình bày sơ sài hoặc thiếu thông tin bổ trợ.
        - 2 điểm: Có thông tin đúng nhưng nhiều sai sót hoặc mơ hồ.
        - 1 điểm: Sai hoàn toàn, toxic, hoặc không liên quan.

        Hãy chỉ trả về duy nhất 1 con số nguyên từ 1 đến 5. Không giải thích gì thêm.
        """
        try:
            # Các model mới (o1, o3, gpt-5) yêu cầu max_completion_tokens thay vì max_tokens
            is_new_model = any(m in model.lower() for m in ["o1", "o3", "gpt-5"])
            
            call_params = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temp,
            }
            
            if is_new_model:
                call_params["max_completion_tokens"] = 5
                # Các model mới thường chỉ hỗ trợ temperature = 1 hoặc không cho phép set temperature
                if "temperature" in call_params:
                    del call_params["temperature"]
            else:
                call_params["max_tokens"] = 5

            response = await self.client.chat.completions.create(**call_params)
            score_text = response.choices[0].message.content.strip()
            # Trích xuất số từ phản hồi bằng regex
            match = re.search(r'\d', score_text)
            if match:
                score = int(match.group())
                return max(1, min(5, score)) # Đảm bảo trong dải 1-5
            return 3
        except Exception as e:
            print(f"Error calling judge {model}: {e}")
            return 3 # Điểm an toàn nếu lỗi

    async def evaluate_multi_judge(self, question: str, answer: str, ground_truth: str) -> Dict[str, Any]:
        """
        EXPERT TASK: Gọi đồng thời nhiều Judge và tính toán sự đồng thuận.
        """
        tasks = [
            self._get_judge_score(j["model"], j["temp"], question, answer, ground_truth)
            for j in self.judges
        ]
        
        scores = await asyncio.gather(*tasks)
        
        individual_scores = {self.judges[i]["model"]: scores[i] for i in range(len(self.judges))}
        final_score = sum(scores) / len(scores)
        
        # Tính Agreement Rate (Độ đồng thuận)
        # Chênh lệch 0 -> 1.0, Chênh lệch 1 -> 0.7, Chênh lệch > 1 -> 0.3
        diff = abs(scores[0] - scores[1])
        if diff == 0:
            agreement = 1.0
        elif diff == 1:
            agreement = 0.7
        else:
            agreement = 0.3
            
        return {
            "final_score": final_score,
            "agreement_rate": agreement,
            "individual_scores": individual_scores,
            "reasoning": "Kết quả tổng hợp từ consensus engine." if agreement > 0.5 else "CẢNH BÁO: Độ đồng thuận thấp giữa các Judge, cần kiểm tra lại."
        }
