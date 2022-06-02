import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, AutoModel

from dialogic.nlu.matchers import PairwiseMatcher

CHITCHAT_MODEL_NAME = 'cointegrated/rut5-small-chitchat'
EMBEDDER_MODEL_NAME = 'cointegrated/rubert-tiny2'

chichat_model = AutoModelForSeq2SeqLM.from_pretrained(CHITCHAT_MODEL_NAME)
chichat_tokenizer = AutoTokenizer.from_pretrained(CHITCHAT_MODEL_NAME)

embedder_model = AutoModel.from_pretrained(EMBEDDER_MODEL_NAME)
embedder_tokenizer = AutoTokenizer.from_pretrained(EMBEDDER_MODEL_NAME)


def respond_with_gpt(text: str):
    inputs = chichat_tokenizer(text, return_tensors='pt').to(chichat_model.device)
    hypotheses = chichat_model.generate(
        **inputs,
        do_sample=True,
        top_p=0.5,
        num_return_sequences=1,
        repetition_penalty=2.5,
        max_length=32,
    )
    return chichat_tokenizer.decode(hypotheses[0], skip_special_tokens=True)


def encode_with_bert(text: str):
    t = embedder_tokenizer(text, padding=True, truncation=True, return_tensors='pt')
    with torch.inference_mode():
        model_output = embedder_model(**{k: v.to(embedder_model.device) for k, v in t.items()})
        embeddings = model_output.last_hidden_state[:, 0, :]
        embeddings = torch.nn.functional.normalize(embeddings)
    return embeddings[0].cpu().numpy()


class VectorMatcher(PairwiseMatcher):
    def __init__(self, text_normalization=None, threshold=0.9, **kwargs):
        super().__init__(text_normalization=text_normalization, threshold=threshold, **kwargs)

    def preprocess(self, text):
        return encode_with_bert(text)

    def compare(self, one, another):
        # dot product of normalized vectors is cosine distance
        return sum(one * another)
