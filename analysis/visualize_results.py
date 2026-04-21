import json
import os
from typing import List, Dict

def load_results(file_path: str) -> List[Dict]:
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.")
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def format_table_row(row: List[str], widths: List[int]) -> str:
    return " | ".join(f"{str(item):<{widths[i]}}" for i, item in enumerate(row))

def visualize_failures(results: List[Dict]):
    if not results:
        print("No results to visualize.")
        return

    # Định nghĩa các cột và độ rộng
    headers = ["STT", "Status", "Retrieval", "Score", "Question Snippet"]
    widths = [4, 10, 10, 6, 60]

    print("\n" + "="*100)
    print(f"{'📊 CHI TIẾT KẾT QUẢ BENCHMARK (ZERO-DEPENDENCY)':^100}")
    print("="*100)
    print(format_table_row(headers, widths))
    print("-" * 100)

    for i, res in enumerate(results):
        status = res.get("status", "fail").upper()
        icon = "✅" if status == "PASS" else "❌"
        
        expected = res.get("expected_retrieval_ids", [])
        retrieved = res.get("retrieved_ids", [])
        
        retrieval_correct = any(rid in retrieved for rid in expected) if expected else True
        ret_status = "OK" if retrieval_correct else "MISS"
        
        score = res["judge"]["final_score"]
        question = res["question"][:57] + "..."

        row = [i+1, f"{icon} {status}", ret_status, f"{score:.1f}", question]
        print(format_table_row(row, widths))

    # Tóm tắt lỗi
    failures = [r for r in results if r.get("status", "fail").lower() == "fail"]
    print("\n" + "="*100)
    print(f"🔥 CÁC CA KẾT QUẢ THẤT BẠI ({len(failures)}/{len(results)}):")
    for i, f in enumerate(failures[:10]): # Chỉ in 10 lỗi đầu tiên cho gọn
        print(f"- Lỗi {i+1}: {f['question']}")
        print(f"  -> Mong đợi: {f.get('expected_retrieval_ids', [])} | Thực tế: {f.get('retrieved_ids', [])}")
    if len(failures) > 10:
        print(f"... và {len(failures)-10} lỗi khác.")
    print("="*100)

def export_markdown(results: List[Dict], output_path: str):
    """Xuất bảng markdown thủ công không cần pandas"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# 🔬 Detailed Diagnostic Report\n\n")
        f.write("| Status | Retrieval | Score | Question | Expected | Retrieved | reasoning |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n")
        
        for res in results:
            icon = "✅" if res["status"].lower() == "pass" else "❌"
            expected = ", ".join(res.get("expected_retrieval_ids", []))
            retrieved = ", ".join(res.get("retrieved_ids", []))
            reasoning = res["judge"]["reasoning"].replace("\n", " ")
            
            f.write(f"| {icon} {res['status'].upper()} | {'OK' if expected in retrieved else 'MISS'} | {res['judge']['final_score']} | {res['question']} | {expected} | {retrieved} | {reasoning} |\n")
    
    print(f"\n✅ Diagnostic report saved to: {output_path}")

if __name__ == "__main__":
    results_path = "reports/benchmark_results.json"
    results = load_results(results_path)
    if results:
        visualize_failures(results)
        export_markdown(results, "reports/diagnostics.md")
