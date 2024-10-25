import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel
from typing import Dict, List, Union, Optional, Tuple


class EntityMatcher:
    def __init__(self, model_path: str = 'dmis-lab/biobert-v1.1', device: str = 'cpu'):
        """
        Args:
            model_path (str, optional): Path to the BioBERT model. Defaults to 'dmis-lab/biobert-v1.1'.
            device (str, optional): The device for the model to run on ('cpu' or 'cuda'). Defaults to 'cpu'.
        """
        self.model_path = model_path
        self.device = device
        self.model: Optional[AutoModel] = None
        self.tokenizer: Optional[AutoTokenizer] = None
        self.embeddings: Optional[Dict[str, Dict[str, Union[str, torch.Tensor]]]] = None

    def load_model(self):
        """
        Load the BioBERT model and tokenizer from the specified model path.

        Returns:
            None
        """
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        self.model = AutoModel.from_pretrained(self.model_path)
        self.model.to(self.device)

    def load_embeddings(self, embedding_file_path: str) -> None:
        """
        Load embeddings from a .pt file and store them in memory.

        Args:
            embedding_file_path (str): Path to the .pt file containing embeddings.

        Returns:
            None
        """
        embeddings = torch.load(embedding_file_path, map_location=torch.device('cpu')) 
        return embeddings
    
    def set_embeddings(self, embeddings: Dict[str, Dict[str, Union[str, torch.Tensor]]]) -> None:
            """
            Set the embeddings manually from an external variable.

            Args:
                embeddings (Dict): Pre-loaded embeddings.

            Returns:
                None
            """
            self.embeddings = embeddings

    def get_topk_entities(
        self, query: str, k: int = 5, embeddings: Optional[Dict[str, Dict[str, Union[str, torch.Tensor]]]] = None
    ) -> List[Tuple[str, str]]:
        """
        Retrieve the top-k entities based on the cosine similarity of the query.

        Args:
            query (str): The input text for which to find similar entities.
            k (int): The number of top similar entities to return.
            embeddings (Dict): The embeddings dictionary to use. 

        Returns:
            List[Tuple[str, str]]: List of tuples containing `Medgraphica_ID` and the corresponding `Name`.
        """
        if self.model is None or self.tokenizer is None:
            raise ValueError("Model and tokenizer must be loaded using `load_model()` before calling this method.")
        if embeddings is None:
            raise ValueError("Embeddings must be provided either as an argument or loaded in the class.")

        inputs = self.tokenizer(query, return_tensors='pt', padding=True, truncation=True).to(self.device)

        with torch.no_grad():
            outputs = self.model(**inputs)

        query_embedding = outputs.last_hidden_state[:, 0, :].cpu()  

        similarities = []
        for med_id, entity_data in embeddings.items():
            entity_embedding = entity_data['embedding']
            similarity_score = F.cosine_similarity(query_embedding, entity_embedding, dim=1)
            similarities.append((med_id, entity_data['Name'], similarity_score.item()))

        top_k_results = sorted(similarities, key=lambda x: x[2], reverse=True)[:k]

        return [(med_id, name) for med_id, name, _ in top_k_results]


