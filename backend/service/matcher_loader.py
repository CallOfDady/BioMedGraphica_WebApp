# backend/service/matcher_loader.py
from backend.service.embedding_matcher import EntityMatcher

matcher = None  # Global singleton

def load_matcher(device: str = "cpu"):
    """Load and return a singleton matcher"""
    global matcher
    if matcher is None:
        print("Loading BioBERT matcher...")
        matcher = EntityMatcher(model_path="dmis-lab/biobert-v1.1", device=device)
        matcher.load_model()
        print("Matcher loaded and cached")
    return matcher
