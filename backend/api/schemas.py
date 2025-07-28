# backend/api/schemas.py

from pydantic import BaseModel
from typing import List, Optional

# ---------------------------
# Request/Response Schemas
# ---------------------------

class EntityConfig(BaseModel):
    feature_label: str
    entity_type: str
    id_type: Optional[str]
    match_mode: str
    file_path: str
    fill0: bool = False

class LabelConfig(BaseModel):
    feature_label: str
    entity_type: str
    id_type: Optional[str]
    file_path: str
    fill0: bool = False

class FinalConfig(BaseModel):
    file_order: Optional[List[str]]
    apply_zscore: bool = False
    edge_types: Optional[List[str]]