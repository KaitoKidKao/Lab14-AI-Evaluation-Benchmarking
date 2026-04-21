from typing import Dict, List, Tuple

class ReleaseGate:
    """
    Hệ thống Auto-Gate tự động quyết định Release hoặc Rollback dựa trên
    các chỉ số đo lường đa chiều: Chất lượng (Quality), Chi phí (Cost), Hiệu năng (Performance).
    """
    def __init__(
        self, 
        min_hit_rate: float = 0.8, 
        max_latency_increase: float = 0.2, 
        max_cost: float = 0.05
    ):
        self.thresholds = {
            "min_hit_rate": min_hit_rate,
            "max_latency_increase": max_latency_increase,
            "max_cost": max_cost
        }
        self.reasons = []

    def evaluate_gate(self, v1_summary: Dict, v2_summary: Dict) -> Tuple[bool, str]:
        """
        Thực hiện so sánh và đưa ra quyết định.
        Trả về: (Is Approved, Full Report)
        """
        self.reasons = []
        v1_metrics = v1_summary["metrics"]
        v2_metrics = v2_summary["metrics"]

        # 1. Kiểm tra Chất lượng (Quality)
        score_delta = v2_metrics["avg_score"] - v1_metrics["avg_score"]
        quality_pass = True
        
        if score_delta < 0:
            quality_pass = False
            self.reasons.append(f"❌ QUALITY: Score decreased by {abs(score_delta):.2f} pts")
        
        if v2_metrics["hit_rate"] < self.thresholds["min_hit_rate"]:
            quality_pass = False
            self.reasons.append(f"❌ QUALITY: Hit Rate {v2_metrics['hit_rate']:.2%} is below threshold ({self.thresholds['min_hit_rate']:.2%})")

        # 2. Kiểm tra Hiệu năng (Performance)
        latency_increase = (v2_metrics["avg_latency"] - v1_metrics["avg_latency"]) / v1_metrics["avg_latency"] if v1_metrics["avg_latency"] > 0 else 0
        perf_pass = True
        if latency_increase > self.thresholds["max_latency_increase"]:
            perf_pass = False
            self.reasons.append(f"⚠️ PERFORMANCE: Latency increased by {latency_increase:.2%} (Threshold: {self.thresholds['max_latency_increase']:.2%})")

        # 3. Kiểm tra Chi phí (Cost)
        cost_pass = v2_metrics["total_cost"] <= self.thresholds["max_cost"]
        if not cost_pass:
            self.reasons.append(f"💰 COST: Total cost ${v2_metrics['total_cost']:.4f} exceeded budget ${self.thresholds['max_cost']:.4f}")

        # Tổng hợp kết quả
        is_approved = quality_pass and perf_pass and cost_pass
        report = self._generate_report(v1_metrics, v2_metrics, is_approved)
        
        return is_approved, report

    def _generate_report(self, v1: Dict, v2: Dict, is_approved: bool) -> str:
        status_icon = "✅" if is_approved else "❌"
        status_text = "APPROVE RELEASE" if is_approved else "BLOCK RELEASE (ROLLBACK)"
        
        report = [
            "=" * 50,
            f"🚀 AUTO-GATE DECISION: {status_text} {status_icon}",
            "=" * 50,
            f"Metric          | V1 Baseline | V2 Current  | Delta / Status",
            "-" * 50,
            f"Avg Score       | {v1['avg_score']:>11.2f} | {v2['avg_score']:>11.2f} | {v2['avg_score']-v1['avg_score']:>+7.2f}",
            f"Hit Rate        | {v1['hit_rate']:>11.2%} | {v2['hit_rate']:>11.2%} | {'PASS' if v2['hit_rate']>=self.thresholds['min_hit_rate'] else 'FAIL'}",
            f"Avg Latency     | {v1['avg_latency']:>10.2f}s | {v2['avg_latency']:>10.2f}s | {(v2['avg_latency']-v1['avg_latency'])/v1['avg_latency']:>+7.2%}",
            f"Total Cost      | ${v1['total_cost']:>10.4f} | ${v2['total_cost']:>10.4f} | {'PASS' if v2['total_cost']<=self.thresholds['max_cost'] else 'FAIL'}",
            "-" * 50,
        ]

        if not is_approved:
            report.append("DETAILED BLOCKING REASONS:")
            for reason in self.reasons:
                report.append(f"- {reason}")
        else:
            report.append("✨ All quality gates passed. System is stable for release.")
        
        report.append("=" * 50)
        return "\n".join(report)
