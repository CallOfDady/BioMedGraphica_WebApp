import json
import os
import re
from typing import Any, Dict, List, Optional

import numpy as np
import torch
import faiss
from transformers import AutoModel, AutoTokenizer


def _normalize_key(text: str) -> str:
    s = "" if text is None else str(text)
    s = s.strip()
    s = re.sub(r"\s+", " ", s)
    return s.lower()


def _mean_pooling(last_hidden_state: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
    mask = attention_mask.unsqueeze(-1).type_as(last_hidden_state)
    summed = (last_hidden_state * mask).sum(dim=1)
    counts = mask.sum(dim=1).clamp(min=1e-6)
    return summed / counts


class BiobertEncoder:
    def __init__(
        self,
        model_path: str = "dmis-lab/biobert-base-cased-v1.2",
        device: Optional[str] = None,
        max_length: int = 128,
        use_fp16: bool = False,
    ):
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"

        self.model_path = model_path
        self.device = device
        self.max_length = int(max_length)
        self.use_fp16 = bool(use_fp16)

        self.tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=True)
        self.model = AutoModel.from_pretrained(model_path)
        self.model.to(self.device)
        self.model.eval()

    @torch.inference_mode()
    def embed(self, texts: List[str]) -> np.ndarray:
        enc = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt",
        )
        enc = {k: v.to(self.device) for k, v in enc.items()}

        amp_enabled = self.device.startswith("cuda") and self.use_fp16
        with torch.amp.autocast('cuda',enabled=amp_enabled):
            out = self.model(**enc)
            pooled = _mean_pooling(out.last_hidden_state, enc["attention_mask"])

        pooled = torch.nn.functional.normalize(pooled, p=2, dim=1)
        return pooled.detach().cpu().to(torch.float32).numpy()

    def embed_one(self, text: str) -> np.ndarray:
        return self.embed([text])


_ENCODER_SINGLETON: Optional[BiobertEncoder] = None


def init_encoder(
    model_path: str = "dmis-lab/biobert-base-cased-v1.2",
    device: Optional[str] = None,
    max_length: int = 128,
    use_fp16: bool = False,
    force_reload: bool = False,
) -> BiobertEncoder:
    global _ENCODER_SINGLETON

    if not force_reload and _ENCODER_SINGLETON is not None:
        same = (
            _ENCODER_SINGLETON.model_path == model_path
            and _ENCODER_SINGLETON.device == (device or _ENCODER_SINGLETON.device)
            and _ENCODER_SINGLETON.max_length == int(max_length)
            and _ENCODER_SINGLETON.use_fp16 == bool(use_fp16)
        )
        if same:
            return _ENCODER_SINGLETON

    _ENCODER_SINGLETON = BiobertEncoder(
        model_path=model_path,
        device=device,
        max_length=max_length,
        use_fp16=use_fp16,
    )
    return _ENCODER_SINGLETON


class EntityMatcher:
    def __init__(
        self,
        entity_type: str,
        index_root_dir: str = "./bmg_alias_faiss",
        encoder: Optional[BiobertEncoder] = None,
    ):
        et = str(entity_type).strip()
        if not et:
            raise ValueError("entity_type is empty.")
        self.entity_type = et

        if encoder is None:
            encoder = init_encoder()
        self.encoder = encoder

        index_dir = os.path.join(index_root_dir, et)
        index_path = os.path.join(index_dir, "alias.index")
        meta_path = os.path.join(index_dir, "meta.json")

        if not os.path.exists(index_path):
            raise FileNotFoundError(f"FAISS index not found: {index_path}")
        if not os.path.exists(meta_path):
            raise FileNotFoundError(f"Meta file not found: {meta_path}")

        self.index_dir = index_dir
        self.index = faiss.read_index(index_path)

        with open(meta_path, "r", encoding="utf-8") as f:
            self.meta = json.load(f)

        self.alias_texts: List[str] = self.meta["alias_texts"]
        self.alias_to_entity: List[str] = self.meta["alias_to_entity"]
        self.alias_to_conn_id: Optional[List[str]] = self.meta.get("alias_to_conn_id")

        self.alias_key_to_indices: Dict[str, List[int]] = {}
        for i, a in enumerate(self.alias_texts):
            k = _normalize_key(a)
            if not k:
                continue
            self.alias_key_to_indices.setdefault(k, []).append(i)

    def _aggregate_by_entity(
        self,
        idxs: np.ndarray,
        scores: np.ndarray,
        topk: int,
        method: str,
        softmax_temp: float,
        return_alias_hits: int,
    ) -> List[Dict[str, Any]]:
        entity_hits: Dict[str, List[tuple]] = {}
        for s, i in zip(scores.tolist(), idxs.tolist()):
            if i < 0:
                continue
            ent = self.alias_to_entity[i]
            entity_hits.setdefault(ent, []).append((float(s), int(i)))

        results: List[Dict[str, Any]] = []
        for ent, hits in entity_hits.items():
            hits.sort(key=lambda x: x[0], reverse=True)

            if method == "max":
                agg = hits[0][0]
            elif method == "softmax_sum":
                vals = np.array([h[0] for h in hits], dtype=np.float32)
                t = max(float(softmax_temp), 1e-6)
                w = np.exp(vals / t)
                agg = float((w * vals).sum() / (w.sum() + 1e-9))
            else:
                raise ValueError("method must be 'max' or 'softmax_sum'")

            best_score, best_i = hits[0]
            item: Dict[str, Any] = {
                "entity_id": ent,
                "score": float(agg),
                "best_alias": self.alias_texts[best_i],
                "best_alias_score": float(best_score),
                "hit_alias_count": int(len(hits)),
            }
            if self.alias_to_conn_id is not None:
                item["conn_id"] = self.alias_to_conn_id[best_i]

            if return_alias_hits > 0:
                alias_hits = []
                for s, i in hits[:return_alias_hits]:
                    hit = {"alias": self.alias_texts[i], "score": float(s)}
                    if self.alias_to_conn_id is not None:
                        hit["conn_id"] = self.alias_to_conn_id[i]
                    alias_hits.append(hit)
                item["alias_hits"] = alias_hits

            results.append(item)

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:topk]

    def match(
        self,
        query: str,
        topk: int = 5,
        top_alias: int = 200,
        method: str = "max",
        softmax_temp: float = 0.05,
        return_alias_hits: int = 0,
        enable_exact: bool = True,
        exact_score: float = 1.0,
    ) -> List[Dict[str, Any]]:
        if enable_exact:
            k = _normalize_key(query)
            idx_list = self.alias_key_to_indices.get(k)
            if idx_list:
                best_i = idx_list[0]
                item: Dict[str, Any] = {
                    "entity_id": self.alias_to_entity[best_i],
                    "score": float(exact_score),
                    "best_alias": self.alias_texts[best_i],
                    "best_alias_score": float(exact_score),
                    "hit_alias_count": int(len(idx_list)),
                    "match_type": "exact_ci",
                }
                if self.alias_to_conn_id is not None:
                    item["conn_id"] = self.alias_to_conn_id[best_i]

                if return_alias_hits > 0:
                    alias_hits = []
                    for i in idx_list[:return_alias_hits]:
                        hit = {"alias": self.alias_texts[i], "score": float(exact_score)}
                        if self.alias_to_conn_id is not None:
                            hit["conn_id"] = self.alias_to_conn_id[i]
                        alias_hits.append(hit)
                    item["alias_hits"] = alias_hits

                return [item]

        q_vec = self.encoder.embed_one(query).astype(np.float32)
        scores, idxs = self.index.search(q_vec, int(top_alias))
        scores = scores[0]
        idxs = idxs[0]

        return self._aggregate_by_entity(
            idxs=idxs,
            scores=scores,
            topk=int(topk),
            method=method,
            softmax_temp=float(softmax_temp),
            return_alias_hits=int(return_alias_hits),
        )

    def match_many(
        self,
        queries: List[str],
        topk: int = 5,
        top_alias: int = 200,
        method: str = "max",
        softmax_temp: float = 0.05,
        return_alias_hits: int = 0,
        enable_exact: bool = True,
        exact_score: float = 1.0,
    ) -> Dict[str, List[Dict[str, Any]]]:
        out: Dict[str, List[Dict[str, Any]]] = {}

        pending: List[str] = []
        pending_pos: List[int] = []

        for qi, q in enumerate(queries):
            if enable_exact:
                k = _normalize_key(q)
                idx_list = self.alias_key_to_indices.get(k)
                if idx_list:
                    best_i = idx_list[0]
                    item: Dict[str, Any] = {
                        "entity_id": self.alias_to_entity[best_i],
                        "score": float(exact_score),
                        "best_alias": self.alias_texts[best_i],
                        "best_alias_score": float(exact_score),
                        "hit_alias_count": int(len(idx_list)),
                        "match_type": "exact_ci",
                    }
                    if self.alias_to_conn_id is not None:
                        item["conn_id"] = self.alias_to_conn_id[best_i]

                    if return_alias_hits > 0:
                        alias_hits = []
                        for i in idx_list[:return_alias_hits]:
                            hit = {"alias": self.alias_texts[i], "score": float(exact_score)}
                            if self.alias_to_conn_id is not None:
                                hit["conn_id"] = self.alias_to_conn_id[i]
                            alias_hits.append(hit)
                        item["alias_hits"] = alias_hits

                    out[q] = [item]
                    continue

            pending.append(q)
            pending_pos.append(qi)

        if pending:
            q_vecs = self.encoder.embed(pending).astype(np.float32)
            scores_mat, idxs_mat = self.index.search(q_vecs, int(top_alias))

            for bi, q in enumerate(pending):
                res = self._aggregate_by_entity(
                    idxs=idxs_mat[bi],
                    scores=scores_mat[bi],
                    topk=int(topk),
                    method=method,
                    softmax_temp=float(softmax_temp),
                    return_alias_hits=int(return_alias_hits),
                )
                out[q] = res

        return out