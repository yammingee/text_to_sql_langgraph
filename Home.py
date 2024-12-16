import streamlit as st

st.set_page_config(
    page_title="Langchain Chatbot",
    page_icon='💬',
    layout='wide'
)

st.header("💬 Data Chatbot with Text2SQL and RAG")
st.write("")
st.write("")
st.write("")
st.write("##### 👉 버전별 구현 내용 보기 ")
st.markdown("""
         ```

        v0.5 text2sql with 질문구체화
            - langchain chaing 적용
            - 비지니스 용어 사전 구축하여 임베딩하여 벡터스토어(FAISS)에 저장 (OpenAIEmbeddings + CacheBackedEmbedding 적용)
            - 사용자 질의와 테이블&컬럼 매핑 가능한 형태로 질문을 구체화한다.
         
        v0.4 text2sql with rag
            - langchain chaining 적용
            - 데이터베이스의 메타정보를 임베딩하여 벡터스토어(FAISS)에 저장 (OpenAIEmbeddings 적용)
            - 데이터베이스의 메타정보 추출을 통해 사용자 질의와 유사도 높은 테이블과 컬럼을 선별한다. (RAG : similarity_search_by_vector)
         
        v0.3 text2sql with few-shot-prompt
            - 랭체인의 sql agent 모듈을 적용.
            - 사용자 쿼리에 few-shot prompt 을 적용
            - example selector 구한하여 적절한 예시를 선별할 수 있도록 하였다.
         
        v0.2 text2sql with sql-agent
            - 랭체인의 sql agent 모듈 으로 구현
            - 에이전트는 먼저 어떤 테이블이 관련성이 있는지 선택한 다음 해당 테이블의 스키마와 몇 개의 샘플 행을 프롬프트에 추가하는 방식이다.
         
        v0.1 text2sql with chain
            - langchain chaining
            - 쿼리 생성 (llm) -> 쿼리 실행 Runnable
        ```
          
         """)