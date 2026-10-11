
import sys
from pathlib import Path

# Add the project root to Python's import path.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from recommendation.recommender import load_papers, recommend_papers


def test_load_papers():
    papers = load_papers()
    assert len(papers) == 37, f"Expected 37 papers, found {len(papers)}"
    assert all("paper" in paper for paper in papers)
    print("PASS: All 37 papers loaded successfully.")


def test_domain_filter():
    papers = recommend_papers(domain="Computer Vision")
    assert papers, "No Computer Vision papers found."
    assert all(
        "computer vision" in paper["domain"].lower()
        for paper in papers
    )
    print(f"PASS: Domain filter returned {len(papers)} papers.")


if __name__ == "__main__":
    test_load_papers()
    test_domain_filter()
    print("\nAll recommendation tests passed!")
