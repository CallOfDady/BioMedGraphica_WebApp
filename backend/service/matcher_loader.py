# backend/service/matcher_loader.py

import os
from typing import Dict, Optional, Tuple

from backend.service.bmg_faiss_matcher import init_encoder, EntityMatcher

_encoder = None
_matchers: Dict[Tuple[str, str], EntityMatcher] = {}


def load_matcher(
    entity_type: str,
    index_root_dir: Optional[str] = None,
    device: str = "cpu",
    model_path: str = "dmis-lab/biobert-base-cased-v1.2",
    max_length: int = 128,
    use_fp16: bool = False,
):
    """
    Load and return a cached FAISS matcher for a specific entity type.
    """
    global _encoder, _matchers

    if not entity_type or not str(entity_type).strip():
        raise ValueError("entity_type is required for FAISS matcher.")

    entity_type = str(entity_type).strip().capitalize()

    if index_root_dir is None:

        index_root_dir = os.getenv("BMG_FAISS_INDEX_ROOT", "../BioMedGraphica-Conn/Embed")

    if _encoder is None:
        print("Loading BioBERT encoder...")
        _encoder = init_encoder(
            model_path=model_path,
            device=device,
            max_length=max_length,
            use_fp16=use_fp16,
        )
        print("Encoder loaded and cached")

    cache_key = (entity_type, os.path.abspath(index_root_dir))
    if cache_key not in _matchers:
        print(f"Loading FAISS matcher for {entity_type} from {index_root_dir} ...")
        _matchers[cache_key] = EntityMatcher(
            entity_type=entity_type,
            index_root_dir=index_root_dir,
            encoder=_encoder,
        )
        print(f"Matcher loaded and cached for {entity_type}")

    return _matchers[cache_key]