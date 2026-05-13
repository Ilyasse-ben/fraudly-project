from unittest.mock import MagicMock

from app.services import rag_service as rag

class FakeCol:
    def count(self):
        return 10
    def query(self, **kwargs):
        print('query called with', kwargs)
        return {
            'documents': [['Doc pertinent sur la fraude documentaire.']],
            'metadatas': [[{'course_id': 'c1', 'chapter_id': 'ch1', 'source_file': 'f.pdf', 'page': 2}]],
            'distances': [[0.12]],
        }

# Monkeypatch functions
rag.get_collection = lambda: FakeCol()
rag.embed_query = lambda q: [0.1] * 768

res = rag.search('fraude documentaire', course_id='c1')
print('RESULT:', res)
print('chunks:', res.chunks)
print('total_found:', res.total_found)
