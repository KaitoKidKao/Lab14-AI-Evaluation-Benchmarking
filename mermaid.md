```
graph TD
    subgraph "Giai đoạn 1: SDG (Dữ liệu)"
        A[Knowledge Base] -->|synthetic_gen.py| B[Golden Dataset]
        B -->|50 test cases| C[Questions + Ground Truth]
    end

    subgraph "Giai đoạn 2: Execution (Thực thi)"
        C --> D[Benchmark Runner]
        D -->|Async Batching| E[Main Agent]
        E -->|Retrieval| F[Contexts + Source IDs]
        E -->|Generation| G[AI Answer]
    end

    subgraph "Giai đoạn 3: Evaluation (Đánh giá)"
        F -->|retrieval_eval.py| H[Hit Rate & MRR]
        G -->|llm_judge.py| I[Multi-Judge Consensus]
        I -->|Judge 1 + Judge 2| J[Agreement Rate]
    end

    subgraph "Giai đoạn 4: Analytics (Báo cáo)"
        H & J --> K[Summary Metrics]
        K -->|main.py| L[Regression Analysis V1 vs V2]
        L --> M[Release Gate: Approve/Block]
        M --> N[reports/summary.json]
    end
```