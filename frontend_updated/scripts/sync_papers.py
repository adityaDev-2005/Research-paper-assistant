"""Regenerate src/data/papers.snapshot.json from the backend's papers.json (read-only)."""
import json, sys
from pathlib import Path
src = Path(sys.argv[1] if len(sys.argv) > 1 else "../data/metadata/papers.json")
raw = json.loads(src.read_text(encoding="utf-8"))
papers = []
for pid, p in raw.items():
    m = p.get("metadata", {})
    papers.append({"paper_id": pid, "title": p.get("paper"), "domain": p.get("domain"),
                   "authors": m.get("authors") or [], "year": m.get("year"), "doi": m.get("doi"),
                   "url": m.get("url"), "source": m.get("source"), "pdf_filename": p.get("pdf_filename")})
out = {"meta": {"generatedFrom": "data/metadata/papers.json", "count": len(papers),
                "note": "Read-only copy of backend metadata. No abstracts or keywords exist in the source."},
       "papers": papers}
dest = Path(__file__).resolve().parent.parent / "src" / "data" / "papers.snapshot.json"
dest.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"wrote {len(papers)} papers -> {dest}")
