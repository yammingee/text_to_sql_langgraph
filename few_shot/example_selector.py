from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from few_shot import few_shot_examples
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS


# 동적 예제 선택기 생성
example_selector = SemanticSimilarityExampleSelector.from_examples(
    few_shot_examples.examples,
    OpenAIEmbeddings(),
    FAISS,
    k=1
)
    
    
