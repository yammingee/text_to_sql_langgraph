from prompts import examples_text

from langchain_community.vectorstores import FAISS
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_openai import OpenAIEmbeddings

my_selector = SemanticSimilarityExampleSelector.from_examples(
    examples_text.examples,
    OpenAIEmbeddings(),
    FAISS,
    k=10,
    input_keys=["input"],
)
