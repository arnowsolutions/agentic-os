"""Hybrid RAG knowledge base for Vapi voice queries.

Combines TF-IDF keyword matching with a lightweight LSA semantic layer
(sklearn TruncatedSVD) for robust retrieval without external API calls.
The vector model is stored in `data/knowledge_vectors.pkl`; deleting it
rebuilds the index.
"""
import glob
import html
import json
import math
import os
import pickle
import re
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ── Paths (relative to this file's location) ──
_BASE = Path(__file__).resolve().parent.parent  # agentic-os/
NOTEBOOKLM_DIR = str(_BASE / "data" / "notebooklm")
KB_INDEX_PATH = str(_BASE / "data" / "knowledge_index.json")
KB_VECTORS_PATH = str(_BASE / "data" / "knowledge_vectors.pkl")
AI_KNOWLEDGE_DIR = str(_BASE.parent / "ai_knowledge_base")
EXTRA_KB_DIRS = [
    str(_BASE.parent / "knowledge-base"),
    str(_BASE.parent / "ai_prompts_and_tools"),
]

# ── Document representation ───────────────────────────────

_documents = None
_doc_index = None  # {term: {doc_id: count}}
_vectorizer = None
_svd = None
_doc_vectors = None


def _clean_text(text: str) -> str:
    """Normalize whitespace and decode HTML entities."""
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _strip_html(raw: str) -> str:
    """Remove scripts/styles/tags and decode entities from HTML."""
    text = re.sub(r"<style[^>]*>.*?</style>", " ", raw, flags=re.DOTALL)
    text = re.sub(r"<script[^>]*>.*?</script>", " ", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    return _clean_text(text)


def _tokenize(text: str) -> list[str]:
    """Convert text to lowercase tokens."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s'\-]", " ", text)
    tokens = text.split()
    stopwords = {
        "the", "a", "an", "is", "was", "are", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will",
        "would", "could", "should", "may", "might", "shall", "can",
        "to", "of", "in", "for", "on", "with", "at", "by", "from",
        "as", "into", "through", "during", "before", "after", "above",
        "below", "between", "out", "off", "over", "under", "again",
        "further", "then", "once", "here", "there", "when", "where",
        "why", "how", "all", "each", "every", "both", "few", "more",
        "most", "other", "some", "such", "no", "nor", "not", "only",
        "own", "same", "so", "than", "too", "very", "just", "also",
        "and", "but", "or", "if", "because", "about", "up", "down",
    }
    return [t for t in tokens if len(t) > 2 and t not in stopwords]


def _load_documents() -> list[dict]:
    """Load all documents into a flat list of {id, title, text, source, space}."""
    global _documents
    if _documents is not None:
        return _documents

    docs = []
    doc_id = 0

    def _add_doc(text: str, title: str, source: str, space: str):
        nonlocal doc_id
        text = _clean_text(text)
        if len(text) < 50:
            return
        docs.append({
            "id": f"kb_{doc_id}",
            "title": title.replace("_", " ")[:80],
            "text": text,
            "source": source,
            "space": space,
        })
        doc_id += 1

    # 1. NotebookLM exports (Montefiore policies, Urology docs)
    if os.path.exists(NOTEBOOKLM_DIR):
        for fpath in glob.glob(f"{NOTEBOOKLM_DIR}/**/*", recursive=True):
            try:
                if fpath.endswith((".md", ".txt")):
                    raw = open(fpath, errors="ignore").read()
                elif fpath.endswith(".html"):
                    raw = _strip_html(open(fpath, errors="ignore").read())
                else:
                    continue
                _add_doc(
                    raw,
                    os.path.basename(fpath).rsplit(".", 1)[0],
                    f"notebooklm/{os.path.basename(fpath)}",
                    "Montefiore Policies",
                )
            except Exception:
                pass

    # 2. AI Knowledge Base
    if os.path.exists(AI_KNOWLEDGE_DIR):
        for fpath in glob.glob(f"{AI_KNOWLEDGE_DIR}/**/*.md", recursive=True):
            try:
                raw = open(fpath, errors="ignore").read()
                _add_doc(
                    raw,
                    os.path.basename(fpath).rsplit(".", 1)[0],
                    os.path.relpath(fpath, AI_KNOWLEDGE_DIR),
                    "AI Knowledge Base",
                )
            except Exception:
                pass

    # 3. Extra knowledge folders
    for extra_dir in EXTRA_KB_DIRS:
        if not os.path.exists(extra_dir):
            continue
        for fpath in glob.glob(f"{extra_dir}/**/*", recursive=True):
            try:
                if fpath.endswith((".md", ".txt")):
                    raw = open(fpath, errors="ignore").read()
                elif fpath.endswith(".html"):
                    raw = _strip_html(open(fpath, errors="ignore").read())
                else:
                    continue
                _add_doc(
                    raw,
                    os.path.basename(fpath).rsplit(".", 1)[0],
                    os.path.relpath(fpath, extra_dir),
                    os.path.basename(extra_dir).replace("-", " ").title(),
                )
            except Exception:
                pass

    _documents = docs
    return docs


def _build_tfidf_index():
    """Build TF-IDF keyword index."""
    global _doc_index
    docs = _load_documents()

    term_doc_freq = Counter()
    doc_terms = {}

    for doc in docs:
        tokens = _tokenize(doc["text"])
        term_counts = Counter(tokens)
        doc_terms[doc["id"]] = term_counts
        for term in term_counts:
            term_doc_freq[term] += 1

    n_docs = len(docs)
    index = defaultdict(dict)

    for doc in docs:
        doc_id = doc["id"]
        term_counts = doc_terms.get(doc_id, Counter())
        max_freq = max(term_counts.values()) if term_counts else 1

        for term, freq in term_counts.items():
            tf = freq / max_freq
            idf = math.log(n_docs / (1 + term_doc_freq.get(term, 1)))
            score = tf * idf
            if score > 0.01:
                index[term][doc_id] = score

    _doc_index = dict(index)
    return index


def _build_semantic_index():
    """Build LSA semantic vectors over the knowledge corpus."""
    global _vectorizer, _svd, _doc_vectors
    docs = _load_documents()
    if len(docs) < 3:
        _vectorizer = None
        _svd = None
        _doc_vectors = None
        return

    texts = [d["text"] for d in docs]
    # Use a token pattern close to our tokenizer but let sklearn strip stop words too
    vectorizer = TfidfVectorizer(
        max_df=0.85,
        min_df=2,
        stop_words="english",
        token_pattern=r"(?u)\b[a-zA-Z0-9][a-zA-Z0-9\-']{2,}\b",
        ngram_range=(1, 2),
        sublinear_tf=True,
    )
    tfidf = vectorizer.fit_transform(texts)

    n_components = min(100, tfidf.shape[1] - 1, len(docs) - 1)
    if n_components < 2:
        _vectorizer = vectorizer
        _svd = None
        _doc_vectors = tfidf
        return

    svd = TruncatedSVD(n_components=n_components, random_state=42)
    doc_vectors = svd.fit_transform(tfidf)

    _vectorizer = vectorizer
    _svd = svd
    _doc_vectors = doc_vectors


def _save_indices():
    """Persist keyword index and semantic model to disk."""
    os.makedirs(os.path.dirname(KB_INDEX_PATH), exist_ok=True)
    with open(KB_INDEX_PATH, "w") as f:
        json.dump(
            {"docs": _load_documents(), "index": {k: dict(v) for k, v in _doc_index.items()}},
            f,
        )
    with open(KB_VECTORS_PATH, "wb") as f:
        pickle.dump({"vectorizer": _vectorizer, "svd": _svd, "doc_vectors": _doc_vectors}, f)


def _load_indices():
    """Load cached indices if present and fresh."""
    global _documents, _doc_index, _vectorizer, _svd, _doc_vectors
    if not os.path.exists(KB_INDEX_PATH):
        return False
    try:
        cached = json.loads(open(KB_INDEX_PATH).read())
        _documents = cached.get("docs", [])
        _doc_index = cached.get("index", {})
    except Exception:
        return False

    if os.path.exists(KB_VECTORS_PATH):
        try:
            with open(KB_VECTORS_PATH, "rb") as f:
                data = pickle.load(f)
            _vectorizer = data.get("vectorizer")
            _svd = data.get("svd")
            _doc_vectors = data.get("doc_vectors")
        except Exception:
            _vectorizer = None
            _svd = None
            _doc_vectors = None
    return True


def _semantic_scores(q: str, docs: list[dict]) -> dict[str, float]:
    """Return {doc_id: cosine_score} for the query using the LSA model."""
    if _vectorizer is None or _doc_vectors is None:
        return {}
    try:
        q_tfidf = _vectorizer.transform([q])
        q_vec = q_tfidf if _svd is None else _svd.transform(q_tfidf)
        sims = cosine_similarity(q_vec, _doc_vectors)[0]
        return {docs[i]["id"]: float(sims[i]) for i in range(len(docs))}
    except Exception:
        return {}


def query(q: str, top_k: int = 5) -> list[dict]:
    """Search knowledge base with hybrid keyword + semantic scoring."""
    if _doc_index is None or _documents is None:
        _build_tfidf_index()
        _build_semantic_index()
        _save_indices()

    docs = _load_documents()
    doc_map = {d["id"]: d for d in docs}

    query_tokens = _tokenize(q)

    # Keyword scores
    keyword_scores = Counter()
    for term in query_tokens:
        if term in _doc_index:
            for doc_id, score in _doc_index[term].items():
                keyword_scores[doc_id] += score

    if not keyword_scores:
        q_lower = q.lower()
        for doc in docs:
            if q_lower in doc["text"].lower()[:2000]:
                keyword_scores[doc["id"]] += 1.0

    # Semantic scores
    sem_scores = _semantic_scores(q, docs)

    # Combine and rank
    combined = Counter()
    all_ids = set(keyword_scores.keys()) | set(sem_scores.keys())
    for doc_id in all_ids:
        k = keyword_scores.get(doc_id, 0.0)
        s = sem_scores.get(doc_id, 0.0)
        # Normalize semantic to roughly keyword scale when keyword is absent
        combined[doc_id] = k + (s * 5.0)

    results = []
    for doc_id, score in combined.most_common(top_k):
        if score <= 0:
            continue
        doc = doc_map.get(doc_id)
        if not doc:
            continue

        text = doc["text"]
        q_lower = q.lower()
        first_term = query_tokens[0] if query_tokens else q_lower
        pos = text.lower().find(first_term)
        if pos >= 0:
            start = max(0, pos - 120)
            end = min(len(text), pos + 320)
            snippet = text[start:end]
        else:
            snippet = text[:320]

        results.append({
            "title": doc["title"],
            "snippet": _clean_text(snippet)[:320],
            "source": doc["source"],
            "space": doc.get("space", ""),
            "score": round(score, 3),
        })

    return results


def query_by_space(q: str, space: str, top_k: int = 3) -> list[dict]:
    """Search within a specific space."""
    docs = _load_documents()
    filtered = [d for d in docs if d.get("space", "").lower() == space.lower()]
    if not filtered:
        return []

    q_lower = q.lower()
    results = []
    for doc in filtered:
        if q_lower in doc["text"].lower()[:2000]:
            text = doc["text"]
            pos = text.lower().find(q_lower)
            start = max(0, pos - 120) if pos >= 0 else 0
            end = min(len(text), start + 320)
            results.append({
                "title": doc["title"],
                "snippet": _clean_text(text[start:end])[:320],
                "source": doc["source"],
                "space": doc.get("space", ""),
                "score": 1.0,
            })
    return results[:top_k]


# ── Preload / cache index ──
if os.path.exists(KB_INDEX_PATH) and os.path.exists(KB_VECTORS_PATH):
    try:
        if _load_indices():
            print(f"Knowledge base loaded: {len(_load_documents())} docs, {len(_doc_index)} terms")
    except Exception:
        _build_tfidf_index()
        _build_semantic_index()
        _save_indices()
else:
    _build_tfidf_index()
    _build_semantic_index()
    _save_indices()
    print(f"Knowledge base built: {len(_load_documents())} docs, {len(_doc_index)} terms")
