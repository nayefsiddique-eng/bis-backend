from abc import ABC, abstractmethod
from typing import Any, List, Dict, Optional

class VectorStoreProvider(ABC):
    @abstractmethod
    async def add_documents(self, documents: List[Dict[str, Any]]) -> List[str]:
        pass

    @abstractmethod
    async def search(self, query: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        pass

class InMemoryVectorStore(VectorStoreProvider):
    def __init__(self):
        self.store: List[Dict[str, Any]] = []

    async def add_documents(self, documents: List[Dict[str, Any]]) -> List[str]:
        added_ids = []
        for doc in documents:
            doc_id = doc.get('id', f'doc_{len(self.store) + 1}')
            entry = {
                'id': doc_id,
                'document_id': doc.get('document_id', 'doc_default'),
                'document_name': doc.get('document_name', 'BIS Standard'),
                'standard_number': doc.get('standard_number', 'IS 1234:2025'),
                'page': doc.get('page', 1),
                'section': doc.get('section', '1.0'),
                'text': doc.get('text', ''),
                'source_type': doc.get('source_type', 'BIS_PDF')
            }
            self.store.append(entry)
            added_ids.append(doc_id)
        return added_ids

    async def search(self, query: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        query_words = set(query.lower().split())
        results = []
        for item in self.store:
            text_words = set(item['text'].lower().split())
            overlap = len(query_words.intersection(text_words))
            score = float(overlap) / max(len(query_words), 1) + 0.5 if overlap > 0 else 0.2
            
            if filters:
                match = True
                for k, v in filters.items():
                    if item.get(k) != v:
                        match = False
                        break
                if not match:
                    continue

            res = item.copy()
            res['score'] = score
            results.append(res)

        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]

_vector_store_instance: Optional[VectorStoreProvider] = None

def get_vector_store() -> VectorStoreProvider:
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = InMemoryVectorStore()
    return _vector_store_instance
