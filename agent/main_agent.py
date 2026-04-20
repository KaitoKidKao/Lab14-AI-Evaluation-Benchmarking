import asyncio
import random
from typing import List, Dict

class MainAgent:
    """
    Đây là Agent mẫu sử dụng kiến trúc RAG đơn giản.
    """
    def __init__(self):
        self.name = "SupportAgent-v1"
        self.doc_ids = ["DOC_REG_001", "DOC_SEC_002", "DOC_TRANS_003", "DOC_CARD_004", "DOC_HELP_005"]

    async def query(self, question: str) -> Dict:
        """
        Mô phỏng quy trình RAG thực tế.
        """
        await asyncio.sleep(0.1) 
        
        # Mô phỏng Retrieval: Chọn ngẫu nhiên 1-2 ID tài liệu
        retrieved = random.sample(self.doc_ids, k=random.randint(1, 2))
        
        return {
            "answer": f"Dựa trên tài liệu hệ thống, tôi xin trả lời câu hỏi '{question}' như sau: [Thông tin phản hồi từ AI].",
            "contexts": ["Nội dung giả lập được trích xuất từ văn bản..."],
            "metadata": {
                "model": "gpt-4o-mini",
                "tokens_used": random.randint(100, 300),
                "sources": retrieved
            }
        }
