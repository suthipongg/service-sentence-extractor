import pytest

from datetime import datetime

from models.extract_model import ExtractorModel, ExtractorListModel

class TestExtractorModel:
    def test_empty_values(self):
        with pytest.raises(ValueError, match="Sentence can't be empty"):
            ExtractorModel(sentence=" ")

    def test_custom_values(self):
        now = datetime.now()
        model = ExtractorModel(sentence="Custom Sentence", created_at=now, counter=5)
        assert model.sentence == "Custom Sentence"
        assert model.created_at == now
        assert model.counter == 5

    def test_auto_set_created_at(self):
        model = ExtractorModel(sentence="Test")
        assert isinstance(model.created_at, datetime)
        assert model.sentence == "Test"
    
class TestExtractorListModel:
    def test_single_sentence(self):
        model = ExtractorListModel(sentences="A single sentence")
        assert model.sentences == ["A single sentence"]

    def test_list_of_sentences(self):
        sentences = ["Sentence 1", "Sentence 2", "Sentence 3"]
        model = ExtractorListModel(sentences=sentences)
        assert model.sentences == sentences
