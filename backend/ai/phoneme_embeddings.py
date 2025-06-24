import torch
from transformers import AutoTokenizer, AutoModel
import eng_to_ipa as G2p

class PhonemeEmbeddingGenerator:
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
        self.bert_model = AutoModel.from_pretrained("bert-base-uncased")
    
    def generate_embedding(self, text):
        text = "hello world"
        # Convert text to phonemes using the G2p instance
        phonemes = G2p.convert(text)
        print(f"Phonemes: {phonemes}")
        # Then tokenize the phonemes
        tokens = self.tokenizer(phonemes, return_tensors="pt", add_special_tokens=False)
        with torch.no_grad():
            outputs = self.bert_model(**tokens)

        phoneme_embeddings = outputs.last_hidden_state
        print("Phoneme Embeddings:", phoneme_embeddings.shape)