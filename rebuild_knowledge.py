#!/usr/bin/env python3
"""Rebuild the knowledge base index.
   Run this after adding NotebookLM exports to:
     /workspace/agentic-os/data/notebooklm/
   Or after adding any new docs to the workspace.
"""
import sys, os, json
sys.path.insert(0, "/workspace/agentic-os/modules")

# Reset the cache so it reloads
import vapi_knowledge as kb
kb._documents = None
kb._doc_index = None

# Force rebuild
docs = kb._load_documents()
print(f"Knowledge base rebuilt: {len(docs)} documents indexed")

# Show sources
sources = {}
for d in docs:
    space = d.get("space", "unknown")
    sources[space] = sources.get(space, 0) + 1
for s, n in sorted(sources.items(), key=lambda x: -x[1]):
    print(f"  {s}: {n} docs")

# Test a query
results = kb.query("Montefiore Urology", top_k=3)
print(f"\nTest query 'Montefiore Urology': {len(results)} results")
for r in results:
    print(f"  [{r['score']}] {r['title'][:60]}")
