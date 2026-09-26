import uuid
from datetime import datetime
from typing import List, Dict, Any
from app.schemas.flashcards import FlashcardItem, FlashcardListResponse
from app.providers.vector_store import get_vector_store

class FlashcardService:
    def __init__(self):
        self.flashcards: Dict[str, FlashcardItem] = {}
        self.vector_store = get_vector_store()
        self._seed_sample_cards()

    def _seed_sample_cards(self):
        sample = FlashcardItem(
            id='fc_sample_1',
            question='What is the mandatory compliance requirement for Household Electrical Appliances?',
            answer='Must carry IS 302-1 certification and conform to safety standards specified under QCO 2023.',
            source_document='IS 302-1 Safety Specification',
            standard_number='IS 302-1:2024',
            page_number=12,
            section='Clause 4.2',
            difficulty='Medium',
            topic='Safety Compliance',
            created_at=datetime.utcnow().isoformat()
        )
        self.flashcards[sample.id] = sample

    async def generate_flashcards(self, document_id: str = None, count: int = 5) -> FlashcardListResponse:
        created_cards = []
        docs = await self.vector_store.search('compliance standard requirement test', top_k=count)
        
        if not docs:
            for i in range(count):
                fc_id = 'fc_' + str(uuid.uuid4())[:8]
                card = FlashcardItem(
                    id=fc_id,
                    question='What are the essential testing norms under Clause ' + str(i + 1) + '?',
                    answer='Sample testing requires minimum tensile strength of 450 MPa and compliance certification.',
                    source_document='BIS Standard Document',
                    standard_number='IS 1000' + str(i) + ':2025',
                    page_number=i + 5,
                    section='Section ' + str(i + 1),
                    difficulty='Medium',
                    topic='Standard Testing',
                    created_at=datetime.utcnow().isoformat()
                )
                self.flashcards[fc_id] = card
                created_cards.append(card)
        else:
            for item in docs[:count]:
                fc_id = 'fc_' + str(uuid.uuid4())[:8]
                card = FlashcardItem(
                    id=fc_id,
                    question='What requirement is defined in ' + item.get('standard_number', 'BIS Standard') + ' Section ' + str(item.get('section', '1.0')) + '?',
                    answer=item.get('text', 'Compliance testing mandatory.')[:180] + '...',
                    source_document=item.get('document_name', 'BIS Document'),
                    standard_number=item.get('standard_number', 'IS 1234:2025'),
                    page_number=item.get('page', 1),
                    section=str(item.get('section', '1.0')),
                    difficulty='Hard',
                    topic='Technical Compliance',
                    created_at=datetime.utcnow().isoformat()
                )
                self.flashcards[fc_id] = card
                created_cards.append(card)

        return FlashcardListResponse(total=len(created_cards), flashcards=created_cards)

    def get_all(self) -> FlashcardListResponse:
        cards = list(self.flashcards.values())
        return FlashcardListResponse(total=len(cards), flashcards=cards)

    def get_by_id(self, fc_id: str) -> FlashcardItem:
        return self.flashcards.get(fc_id)

    def delete_by_id(self, fc_id: str) -> bool:
        if fc_id in self.flashcards:
            del self.flashcards[fc_id]
            return True
        return False

_flashcard_service = None

def get_flashcard_service() -> FlashcardService:
    global _flashcard_service
    if _flashcard_service is None:
        _flashcard_service = FlashcardService()
    return _flashcard_service
