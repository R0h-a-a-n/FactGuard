
Technologies, MVP cut, and final cut are below. Keep it modular and event-driven.

# Core Technologies

**Data ingestion**

- Reddit API via PRAW (Python). Backoff + retry.
    
- Optional: Reddit WebSocket proxies or Pushshift fallback.
    
- Rate-limit guard: `tenacity`, token bucket.
    

**Streaming backbone**

- Apache Kafka.
    
- Schema Registry with **Avro** or **Protobuf**.
    
- Topic design: `raw_comments_stream`, `topic_models`, `extracted_claims`, `rag_evaluations`, `misinfo_alerts`, `dashboard_events`.
    

**Stream processing**

- Python (Faust) or Kafka Streams (Java) for light transforms.
    
- Consumer groups per microservice.
    

**NLP/LLM**

- Lightweight: spaCy + `keybert` for keywords.
    
- Topic modeling: BERTopic or Online LDA.
    
- Claim/entity extraction: OpenAI / Mistral / Llama via vLLM or TGI.
    
- RAG: LangChain or LlamaIndex.
    
- Vector DB: **Qdrant** or **PGVector**; ingestion from trusted sources (Reuters, AP, gov advisories).
    

**Backend & delivery**

- FastAPI for REST + WebSockets (or Server-Sent Events).
    
- Auth: API Keys or JWT for admin dashboard.
    

**Frontend**

- Streamlit for fastest MVP; React + WebSockets for final.
    

**MLOps & Ops**

- Docker for all services.
    
- Orchestration: Kubernetes (final) or Docker Compose (MVP).
    
- CI/CD: GitHub Actions.
    
- Monitoring: Prometheus + Grafana; logs: OpenSearch/ELK.
    
- Tracing: OpenTelemetry.
    
- Caching: Redis.
    
- Storage: Postgres (events metadata), S3-compatible object store (artifacts).
    

**Quality & safety**

- Moderation: heuristic + LLM safety classifier.
    
- PII scrubber before persistence.
    
- Integrity scores with calibrated thresholds.
    

---

# MVP (scope that proves value)

**Goal:** Live pipeline from Reddit → dashboard with real-time topics and basic misinfo flags.

**Components**

1. **Producer**: Python + PRAW → `raw_comments_stream` (Avro schema: `id, subreddit, created_utc, body, author, permalink`).
    
2. **Consumer A: Topic Modeler**
    
    - BERTopic over rolling window (e.g., last 1–5k comments).
        
    - Emits `{topic_label, top_terms, support, timestamp}` → `topic_models`.
        
3. **Consumer B: Claim Extractor (LLM-light)**
    
    - Prompt: extract factual claims + entities.
        
    - Emits `{comment_id, claim_text, entities, confidence}` → `extracted_claims`.
        
4. **Consumer C: RAG Verifier (minimal)**
    
    - Vector DB preloaded with 200–500 curated articles for the ongoing event.
        
    - LangChain RAG returns `{claim_id, matched_sources[], rationale, verdict ∈ {supported, disputed, unknown}, score}` → `rag_evaluations`.
        
5. **Alert Aggregator**
    
    - Joins claim + RAG → `misinfo_alerts` when `verdict=disputed` or low support with high spread.
        
6. **FastAPI Gateway**
    
    - Subscribes to `topic_models` and `misinfo_alerts`.
        
    - Exposes `/ws` to push updates.
        
7. **Dashboard (Streamlit)**
    
    - Panels: live comments, trending topics (bar/line over time), alerts table with evidence links.
        

**Operational must-haves**

- Docker Compose.
    
- Basic metrics: ingestion rate, consumer lag, alert counts.
    
- Simple secrets via `.env`.
    

**What you can demo**

- Start an event keyword.
    
- Watch themes evolve.
    
- See flagged claims with linked sources and LLM rationale.
    

---

# Final Project (production-grade)

**Scale & robustness**

- Kubernetes deployment with Helm.
    
- Horizontal autoscaling for consumers.
    
- Exactly-once(ish) semantics with idempotent producers and transactional writes where needed.
    

**Data & models**

- Multi-event support with per-event vector indexes.
    
- Online topic modeling with drift detection.
    
- Dedicated NER + claim detection model (fine-tuned) behind vLLM/TGI.
    
- RAG over multi-corpus: news wires, gov advisories, WHO/UN, verified fact-check datasets.
    
- Source quality weighting and recency decay.
    

**Advanced verification**

- Multi-agent adjudication: two independent LLM chains + majority vote.
    
- Citation enforcement: answer must include explicit source spans.
    
- Calibration: Platt/temperature scaling for a stable **misinformation risk score** in [0,1].
    

**Trust, safety, compliance**

- PII removal, profanity filters, geo restrictions.
    
- Audit logs for each alert (inputs, retrieved docs, prompts, outputs, hashes).
    
- Model cards and data lineage.
    

**Observability**

- Full Grafana dashboards: lag, throughput, costs, model latency, RAG hit rate, hallucination proxy metrics.
    
- OpenTelemetry traces across producer→consumers→RAG→API.
    

**Frontend (React)**

- Real-time timeline with topic evolution.
    
- Alert drill-downs: claim text, retrieved passages, verdict, confidence, citations.
    
- Faceted filters by topic, entity, time, verdict.
    
- Admin panel for source curation and threshold tuning.
    

**Security & access**

- OAuth for analyst users.
    
- RBAC: viewer vs curator vs admin.
    
- Signed WebSocket tokens.
    

**Data lifecycle**

- Tiered retention: hot Kafka topics 7–14 days, compacted topics for aggregates, cold storage to S3.
    
- GDPR-style delete on request (hash-addressable records).
    

**Cost controls**

- Dynamic sampling under surge.
    
- Batch RAG for duplicate claims.
    
- Cache embeddings and retrieval results.
    

---

# Minimal schemas (Avro/Protobuf hints)

- `RawComment`: `comment_id, event_id, body, author, subreddit, created_utc, permalink`
    
- `TopicModel`: `event_id, topic_id, label, terms[], weight, window_start, window_end`
    
- `Claim`: `claim_id, comment_id, event_id, text, entities[], confidence`
    
- `RagEval`: `claim_id, sources[{url, title, snippet, score}], verdict, rationale, score`
    
- `Alert`: `alert_id, claim_id, event_id, verdict, risk_score, created_utc`

## Suggested service layout:

/aura
  /ingestion          # reddit-producer (Python)
  /processors
    /topic-modeler    # faust/kstreams
    /claim-extractor  # llm caller
    /rag-verifier     # retriever + llm judge
    /alert-aggregator
  /gateway            # fastapi websockets + rest
  /frontend           # streamlit (mvp) or react (final)
  /infra              # docker, helm, terraform, grafana dashboards
