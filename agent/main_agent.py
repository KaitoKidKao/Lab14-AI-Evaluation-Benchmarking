import asyncio
import os
from typing import List, Dict
from openai import AsyncOpenAI
from dotenv import load_dotenv
from langfuse import observe, Langfuse

load_dotenv()

class MainAgent:
    """
    Agent thực hiện RAG bằng cách sử dụng OpenAI API và dữ liệu từ knowledge_base.txt.
    Tích hợp Langfuse để Observability và Prompt Management.
    """
    def __init__(self):
        self.name = "SmartBank-Expert-Agent"
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.langfuse = Langfuse()
        self.kb_path = "data/knowledge_base.txt"
        self._knowledge_base = self._load_kb()

    def _load_kb(self) -> str:
        try:
            with open(self.kb_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return "Tài liệu ngân hàng không khả dụng."

    @observe()
    async def query(self, question: str, prompt_label: str = "production", prompt_override: str = None) -> Dict:
        """
        Thực hiện quy trình RAG:
        1. Lấy context từ KB.
        2. Lấy prompt từ Langfuse Management (hoặc override).
        3. Gọi OpenAI để sinh câu trả lời.
        """
        context = self._knowledge_base
        
        system_prompt = None
        
        # 1. Ưu tiên prompt_override (dùng cho thử nghiệm nhanh trong code)
        if prompt_override:
            system_prompt = prompt_override.replace("{{context}}", context)
        else:
            # 2. Lấy Prompt từ Langfuse (Prompt Management) dựa trên Label
            try:
                langfuse_prompt = self.langfuse.get_prompt("rag_agent_prompt", label=prompt_label)
                system_prompt = langfuse_prompt.compile(context=context)
            except Exception:
                # Fallback nếu chưa tạo prompt trên Langfuse
                system_prompt = f"Bạn là chuyên gia tư vấn SmartBank. Hãy trả lời câu hỏi dựa trên tài liệu sau:\n\n{context}"
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ],
                temperature=0,
                max_tokens=300
            )
            
            answer = response.choices[0].message.content
            tokens = response.usage.total_tokens
            
            # Trích xuất source IDs từ câu hỏi/context (giả lập logic retrieval)
            # Trong thực tế sẽ dùng Vector Search để lấy ID cụ thể
            retrieved = []
            if "đăng ký" in question.lower(): retrieved.append("DOC_REG_001")
            if "mật khẩu" in question.lower(): retrieved.append("DOC_SEC_002")
            if "chuyển tiền" in question.lower(): retrieved.append("DOC_TRANS_003")
            if "thẻ" in question.lower(): retrieved.append("DOC_CARD_004")
            if "khiếu nại" in question.lower(): retrieved.append("DOC_HELP_005")

            return {
                "answer": answer,
                "contexts": [context[:200] + "..."], # Chỉ trả về một đoạn context demo
                "metadata": {
                    "model": "gpt-4o-mini",
                    "tokens_used": tokens,
                    "sources": retrieved if retrieved else ["DOC_GENERAL"]
                }
            }
        except Exception as e:
            return {
                "answer": f"Lỗi gọi API: {str(e)}",
                "contexts": [],
                "metadata": {"model": "error", "tokens_used": 0, "sources": []}
            }
