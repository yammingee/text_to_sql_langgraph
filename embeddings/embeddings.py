import faiss
import numpy as np

from langchain_openai import OpenAIEmbeddings
from sklearn.preprocessing import normalize
from sklearn.metrics.pairwise import cosine_similarity

# 임베딩 생성 함수
def generate_embeddings(text_chunks):
    # 기본 1536차원 임베딩 -> 1024차원으로 줄임
    embeddings_model = OpenAIEmbeddings(model="text-embedding-3-small", dimensions=1024)
    embeddings = [embeddings_model.embed_query(chunk) for chunk in text_chunks]
    return np.array(embeddings)

# FAISS 저장소 로컬 저장 및 인덱스 생성
def create_faiss_index(embeddings, dim=1024):
    # faiss 저장소 인덱스 생성
    index = faiss.IndexFlatL2(dim)  # L2 거리(유클리디안) 기반 인덱스 생성
    normalized_embeddings = normalize(embeddings)  # 정규화 수행 (선택적)
    index.add(normalized_embeddings)  # 벡터 추가

    # faiss 로컬 저장소에 저장
    faiss_file_path = "faiss_index.idx"
    faiss.write_index(index, faiss_file_path)
    print(f"FAISS index saved to: {faiss_file_path}")

    # 저장된 파일에서 인덱스를 로드 (테스트)
    loaded_index = faiss.read_index(faiss_file_path)
    print(f"FAISS index loaded. Total vectors: {loaded_index.ntotal}")
    return loaded_index


# 유사한 문서 검색 함수
def search_faiss_index(index, query_embedding, top_k=3):
    query_embedding = np.array(query_embedding)
    # query_embedding이 2차원인지 확인 (필요 시 차원 수정)
    if query_embedding.ndim == 1:
        query_embedding = query_embedding.reshape(1, -1)  # (1, 1024)로 변환
    elif query_embedding.ndim > 2:
        raise ValueError("query_embedding has too many dimensions")
    # 정규화 및 유사도 검색 수행
    query_embedding = normalize(query_embedding)
    distances, indices = index.search(query_embedding, top_k)

    # 검색 결과 후처리 (예: 유사도 점수 재계산)
    distances = 1 - distances  # FAISS는 기본적으로 L2 거리 사용, 유사도로 변환
    print(f"distances : {distances}")

    return distances[0], indices[0]

