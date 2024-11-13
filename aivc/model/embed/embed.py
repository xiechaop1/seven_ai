from sentence_transformers import SentenceTransformer
from sentence_transformers.quantization import quantize_embeddings
from typing import List, Optional, Dict
import numpy as np
from aivc.config.config import settings, L
import time


class EmbedModel:
    V1 = 'V1'

    models: Dict[str, SentenceTransformer] = {}
    
    def __init__(self, version:Optional[str]=None):
        self._load_model(EmbedModel.V1, settings.EMBEDDING_MODEL_V1)

    def _load_model(self, version: str, model_name: str):
        if version not in EmbedModel.models:
            start_time = time.time()
            EmbedModel.models[version] = SentenceTransformer(model_name)
            L.debug(f"EmbedModel init model:{model_name} cost time:{int((time.time()-start_time)*1000)}ms")

    def _get_model(self, version) -> SentenceTransformer:
        return EmbedModel.models[version]

    def embed(self, 
            query_texts: List[str], 
            normalize_embeddings=True, 
            version=V1, 
            batch_size: int = 32,
            is_numpy=False):
        model = self._get_model(version)
        embeddings = model.encode(query_texts, 
                batch_size=batch_size,
                normalize_embeddings=normalize_embeddings)
        if is_numpy:
            return embeddings
        return embeddings.tolist()

    def embed_keyword_quantize(self, 
            query_texts: List[str], 
            normalize_embeddings=True, 
            version=V1, 
            batch_size: int = 128,
            precision="int8",
            ranges: Optional[np.ndarray] = None):
        model = self._get_model(version)
        embeddings = model.encode(query_texts, 
                batch_size=batch_size,
                normalize_embeddings=normalize_embeddings)
        
        quant_embeddings = quantize_embeddings(
            embeddings,
            precision=precision,
            ranges=ranges,
        )
        return quant_embeddings.tolist()

    def score(self, query_text: str, target_texts: List[str], normalize_embeddings=True, version=V1):
        if not target_texts:
            return []
        model = self._get_model(version)
        query_emb = model.encode([query_text], normalize_embeddings=normalize_embeddings)
        text_embs = model.encode(target_texts, normalize_embeddings=normalize_embeddings)
        similarity = query_emb @ text_embs.T
        return similarity[0]

    def score_list(self, query_texts: List[str], target_texts: List[str], normalize_embeddings=True, version=V1):
        if not target_texts:
            return np.empty((len(query_texts), 0))
        model = self._get_model(version)
        query_embs = model.encode(query_texts, normalize_embeddings=normalize_embeddings)
        text_embs = model.encode(target_texts, normalize_embeddings=normalize_embeddings)
        similarity = query_embs @ text_embs.T
        return similarity
    
if __name__ == "__main__":
    scorer = EmbedModel()

    texts1 = ["胡子长得太快怎么办？"]
    texts2 = ["怎样使胡子不浓密！", "香港买手表哪里好", "在杭州手机到哪里买"]

    similarity = scorer.score(texts1[0], texts2)
    print(similarity)
