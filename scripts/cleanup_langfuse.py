import os
from langfuse import Langfuse
from dotenv import load_dotenv

def cleanup_traces():
    load_dotenv()
    
    langfuse = Langfuse(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        host=os.getenv("LANGFUSE_HOST")
    )

    print("🔍 Đang kết nối tới Langfuse để lấy danh sách Trace...")
    
    # Lấy danh sách các traces mới nhất
    try:
        # Sử dụng .api.trace.list cho các phiên bản Langfuse SDK mới
        traces = langfuse.api.trace.list(limit=100)
        
        if not traces or not traces.data:
            print("✅ Không có Trace nào để xóa.")
            return

        trace_ids = [t.id for t in traces.data]
        count = len(trace_ids)
        
        print(f"🗑️ Đang xóa {count} traces mới nhất...")
        
        for tid in trace_ids:
            langfuse.api.trace.delete(trace_id=tid)
            
        print(f"✅ Đã xóa thành công {count} traces.")
    except Exception as e:
        print(f"❌ Có lỗi khi truy cập API: {e}")
        print("💡 Gợi ý: Hãy thử xóa trực tiếp trên Dashboard nếu API bị giới hạn.")

if __name__ == "__main__":
    cleanup_traces()
