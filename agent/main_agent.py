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
            
            # Trích xuất source IDs từ câu hỏi/context (giả lập logic retrieval nâng cao)
            keywords = {
                "đăng ký": "DOC_REG_001", "ekyc": "DOC_REG_001", "cccd": "DOC_REG_001", "hộ chiếu": "DOC_REG_001",
                "mật khẩu": "DOC_SEC_002", "password": "DOC_SEC_002", "quên mật khẩu": "DOC_SEC_002", "khóa tài khoản": "DOC_SEC_002",
                "chuyển tiền": "DOC_TRANS_003", "hạn mức": "DOC_TRANS_003", "napas": "DOC_TRANS_003", "phí chuyển tiền": "DOC_TRANS_003",
                "thẻ": "DOC_CARD_004", "platinum": "DOC_CARD_004", "tín dụng": "DOC_CARD_004", "miễn lãi": "DOC_CARD_004",
                "khiếu nại": "DOC_HELP_005", "tổng đài": "DOC_HELP_005", "mất thẻ": "DOC_HELP_005", "1900 1234": "DOC_HELP_005",
                "tiết kiệm": "DOC_SAVE_006", "sổ tiết kiệm": "DOC_SAVE_006", "lãi suất": "DOC_SAVE_006", "rút trước hạn": "DOC_SAVE_006",
                "otp": "DOC_SEC_007", "xác thực": "DOC_SEC_007", "smart otp": "DOC_SEC_007", "sms otp": "DOC_SEC_007",
                "quốc tế": "DOC_INT_008", "swift": "DOC_INT_008", "ngoại tệ": "DOC_INT_008", "nhận tiền nước ngoài": "DOC_INT_008",
                "vay": "DOC_LOAN_009", "ô tô": "DOC_LOAN_009", "giải ngân": "DOC_LOAN_009", "vay tiêu dùng": "DOC_LOAN_009",
                "app": "DOC_APP_010", "thanh toán": "DOC_APP_010", "qr pay": "DOC_APP_010", "hóa đơn": "DOC_APP_010",
                "doanh nghiệp": "DOC_CORP_011", "sme": "DOC_CORP_011", "payroll": "DOC_CORP_011", "chi lương": "DOC_CORP_011",
                "phí cũ": "DOC_OLD_999", "2023": "DOC_OLD_999", "hết hiệu lực": "DOC_OLD_999"
            }
            
            retrieved = []
            q_lower = question.lower()
            for key, doc_id in keywords.items():
                if key in q_lower:
                    retrieved.append(doc_id)

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
