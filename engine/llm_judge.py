import os
import asyncio
import json
import re
import random
from typing import List, Dict, Any
from openai import AsyncOpenAI
from dotenv import load_dotenv
from langfuse import observe
from langfuse import Langfuse

load_dotenv()

class LLMJudge:
    """
    Hệ thống Multi-Judge để chấm điểm câu trả lời của Agent.
    Tích hợp Langfuse để Observability và Prompt Management.
    """
    def __init__(self, models: List[str] = ["gpt-4o-mini", "gpt-5-nano"]):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.langfuse = Langfuse()
        self.models = models
        self.judges = [
            {"model": models[0], "temp": 0.0},
            {"model": models[1], "temp": 0.7}
        ]

    @observe()
    async def _get_judge_score(self, model: str, temp: float, question: str, answer: str, ground_truth: str, history: List[Dict] = None) -> Dict[str, Any]:
        """
        Gọi API OpenAI để lấy điểm số và ý kiến giải thích từ một Judge.
        """
        history_text = ""
        if history:
            history_text = "Lịch sử hội thoại:\n" + "\n".join([f"{m['role']}: {m['content']}" for m in history]) + "\n\n"

        # 1. Lấy Prompt từ Langfuse
        try:
            langfuse_prompt = self.langfuse.get_prompt("llm_judge_prompt")
            prompt = langfuse_prompt.compile(
                question=question, 
                answer=answer, 
                ground_truth=ground_truth,
                history=history_text
            )
        except Exception:
            # Fallback
            prompt = f"""
            Bạn là một chuyên gia đánh giá chất lượng AI. Hãy chấm điểm câu trả lời của AI dựa trên Ground Truth và ngữ cảnh hội thoại.
            
            {history_text}
            Câu hỏi hiện tại: {question}
            Câu trả lời của AI: {answer}
            Ground Truth: {ground_truth}
            
            Tiêu chí chấm điểm (1-5):
            - 5 điểm: Hoàn hảo, chính xác 100%, đúng ngữ cảnh.
            - 4 điểm: Chính xác nhưng diễn đạt chưa tốt.
            - 3 điểm: Đúng ý chính nhưng thiếu sót thông tin quan trọng.
            - 2 điểm: Có sai sót kiến thức hoặc mơ hồ.
            - 1 điểm: Sai hoàn toàn hoặc không liên quan.

            Yêu cầu output định dạng JSON:
            {{
                "score": <số nguyên 1-5>,
                "reasoning": "<giải thích ngắn gọn trong 1 câu>"
            }}
            """
        
        # Sửa lỗi OpenAI 400: Luôn đảm bảo có chữ 'json' trong prompt khi dùng json_object mode
        if "json" not in prompt.lower():
            prompt += "\n\nIMPORTANT: Your response must be a valid JSON object."
        
        try:
            is_new_model = any(m in model.lower() for m in ["o1", "o3", "gpt-5"])
            call_params = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temp,
                "response_format": { "type": "json_object" } if not is_new_model else None
            }
            if is_new_model:
                call_params["max_completion_tokens"] = 300
                if "temperature" in call_params: del call_params["temperature"]
            else:
                call_params["max_tokens"] = 300

            response = await self.client.chat.completions.create(**call_params)
            content = response.choices[0].message.content.strip()
            
            # Parse JSON safely
            try:
                data = json.loads(content)
                return {
                    "score": int(data.get("score", 3)),
                    "reasoning": data.get("reasoning", "No reasoning provided.")
                }
            except:
                # Fallback extraction
                score_match = re.search(r'\d', content)
                return {
                    "score": int(score_match.group()) if score_match else 3,
                    "reasoning": content[:200]
                }
        except Exception as e:
            print(f"Error calling judge {model}: {e}")
            return {"score": 3, "reasoning": f"Error: {str(e)}"}

    @observe()
    async def evaluate_multi_judge(self, question: str, answer: str, ground_truth: str, history: List[Dict] = None) -> Dict[str, Any]:
        """
        Gọi đồng thời nhiều Judge và trả về kết quả chi tiết.
        """
        tasks = [
            self._get_judge_score(j["model"], j["temp"], question, answer, ground_truth, history)
            for j in self.judges
        ]
        
        judge_outputs = await asyncio.gather(*tasks)
        scores = [d["score"] for d in judge_outputs]
        
        individual_results = {}
        for i, output in enumerate(judge_outputs):
            model_name = self.judges[i]["model"]
            individual_results[model_name] = output
            
        final_score = sum(scores) / len(scores)
        
        # Xác định status: consensus (đồng thuận) hoặc conflict (mâu thuẫn)
        diff = abs(scores[0] - scores[1])
        if diff == 0:
            agreement = 1.0
            status = "consensus"
        elif diff == 1:
            agreement = 0.7
            status = "consensus"
        else:
            agreement = 0.3
            status = "conflict"
            
        return {
            "final_score": final_score,
            "agreement_rate": agreement,
            "individual_results": individual_results,
            "status": status,
            "reasoning": "Kết quả tổng hợp từ consensus engine."
        }
