import streamlit as st
import pandas as pd
import numpy as np

from my_utils import utils as utils
from my_utils import db_utils as db_utils
from embeddings import embeddings
from preprocessing import table as preProcessedTableData
from prompts import rag_prompt as rag_prompt
from prompts import generator_sql_prompt as generator_sql_prompt
from langchain_community.callbacks import StreamlitCallbackHandler
from langchain.chains import LLMChain
from langchain_community.utilities import SQLDatabase

from sqlalchemy import text
from prompts import sql_friendly_question_prompt
from prompts import generator_sql_with_few_shot_prompt

st.set_page_config(page_title="ChatSQL", page_icon="🛢")
st.header('Chat MyDB 💬')



class ChatMyDBClass:

    # 클래스 변수 선언
    llm = None
    db = None
    engine = None
    db_connect = None
    table_info = None
    structured_table_info_texts = None
    meta_data_embedding = None
    meta_data_faiss_index = None
    terms_list = None
    few_shot_examples = None
    enum_list = None

    @classmethod
    def initialize(cls):
        utils.sync_st_session()

        # llm 설정 하기
        if cls.llm is None:
            cls.llm = utils.configure_llm()
            print(f"init - llm 설정 완료")

        # db 연결
        if cls.db is None:
            cls.db = utils.configure_db('USE_DBAAS_DB')
            print(f"init - 데이터 베이스 연동 완료")

        # SQLDatabase 엔진 가져오기
        if cls.engine is None:
            cls.engine = SQLDatabase(cls.db)
            print(f"init - 데이터 베이스 엔진 가져오기 완료")
        
        # db 연결 후 테이블 메타 정보 가져오기
        if cls.table_info is None:
            cls.table_info = preProcessedTableData.get_table_info(cls.db)
            print(f"init - 테이블 구조 가져오기 완료")

        # 테이블 메타 정보 구조화 처리
        if cls.structured_table_info_texts is None:
            cls.structured_table_info_texts = preProcessedTableData.structured_tables(cls.table_info)
            print(f"init - 테이블 구조화 완료")

        # 테이블 메타 정보 임베딩
        if cls.meta_data_embedding is None:
            cls.meta_data_embedding = embeddings.generate_embeddings(cls.structured_table_info_texts)
            print(f"init - 테이블 임베딩 완료")

        # 벡터 저장소에 인덱스 추가
        if cls.meta_data_faiss_index is None:
            cls.meta_data_faiss_index = embeddings.create_faiss_index(cls.meta_data_embedding)
            print(f"init - 벡터저장소 인덱스 추가 완료")
    
        # 비지니스 용어 사전 로딩
        if cls.terms_list is None:
            cls.terms_list = utils.getBusinessTerm()
            print(f"init - 비지니스 용어 사전 로딩 완료")
        
        # few_shot_example 로딩
        if cls.few_shot_examples is None:
            cls.few_shot_examples = utils.getFewShotExamples()
            print(f"init - 퓨샷 예제 로딩 완료")

        # enum 데이터 추출
        if cls.enum_list is None:
            cls.enum_list = utils.getEnumDatas()
            print(f"enum 데이터 추출 완료")


@utils.enable_chat_history 
def main():
    ## 사용자 디비 추가
    radio_opt = ['Use My db - MySQL (wepljec)']
    selected_opt = st.sidebar.radio(
        label='Choose Database suitable option',
        options=radio_opt
    )

    if radio_opt.index(selected_opt) == 0:
        db_uri = 'USE_DBAAS_DB'
    
    if not db_uri:
        st.error("Please enter database URI to continue!")
        st.stop()

    # Streamlit의 전역 상태를 통해 초기화 상태 확인
    if "initialized" not in st.session_state:
        ChatMyDBClass.initialize()
        st.session_state["initialized"] = True
        print("===== ChatMyDBClass initialized =====")

    if ChatMyDBClass.engine._engine.connect:
        with st.sidebar.expander('Database tables', expanded=True):
            st.info('\n- '+'\n- '.join(ChatMyDBClass.engine.get_usable_table_names()))
    else:
        st.error("Please enter database URI to continue!")
        st.stop()
    

    ## 사용자 인터페이스 설정
    user_query = st.chat_input(placeholder="Ask me anything!")

    if user_query:
        st.session_state.messages.append({"role": "user", "content": user_query})
        st.chat_message("user").write(user_query)
        
        with st.chat_message("assistant"):
            with st.spinner("답변을 생성하는 중입니다"):                
                try:
                    ################################
                    # 1.질문구체화 (비지니스 용어사전 -> 질문구체화 chain)
                    # LLM 초기화 및 체인 생성
                    chain = LLMChain(prompt=sql_friendly_question_prompt.get_prompt(), llm=ChatMyDBClass.llm, output_key="sql_friendly_question")
                    sql_friendly_question = chain.run({"question": user_query, "terms": ChatMyDBClass.terms_list})
                    print(f"1. Rephrased SQL-friendly Question: {sql_friendly_question}")

                    # Step 1: 사용자 질의 SQL-friendly하게 재구성하여 표시
                    with st.expander("Step 1: Rephrased SQL-friendly Question", expanded=True):
                        st.code(sql_friendly_question)



                    ################################
                    # 2. 테이블 및 컬럼 정보 추출
                    # 재구성된 사용자 질의 임베딩 생성
                    rephrased_embedding = embeddings.generate_embeddings([sql_friendly_question])
                    # 테이블 메타정보 벡터저장소에서 재구성된 사용자 질의와 유사도가 높은 테이블 추출
                    # FAISS를 통해 초기 유사 테이블 검색
                    distances, indices = embeddings.search_faiss_index(ChatMyDBClass.meta_data_faiss_index, rephrased_embedding)
                    # 검색된 테이블을 인덱스로 매핑
                    selected_tables = [ChatMyDBClass.structured_table_info_texts[i] for i in indices]
                    # 테이블 이름 추출
                    selected_table_names = db_utils.extract_table_names(selected_tables)
                    print(f"2. Selected Tables: {selected_table_names}")

                    # Step 2: 관련 테이블 표시
                    with st.expander("Step 2: Selected Tables", expanded=True):
                        st.write(selected_table_names)
                    



                    ################################
                    # 3. Few-Shot Query 적용
                    # 재구성된 질문과 유사한 예제 검색
                    example_embeddings = embeddings.generate_embeddings([ex["question"] for ex in ChatMyDBClass.few_shot_examples])
                    few_shot_examplte_index = embeddings.create_faiss_index(example_embeddings)
                    distances, indices = few_shot_examplte_index.search(np.array(rephrased_embedding), 1)
                    closest_example = ChatMyDBClass.few_shot_examples[indices[0][0]]

                    print(f"3. Selected Few-shot Example: {closest_example}")


                    ################################
                    # 4. 쿼리생성
                    query_chain = LLMChain(prompt=generator_sql_with_few_shot_prompt.get_prompt(), llm=ChatMyDBClass.llm, output_key="generated_sql")
                    # SQL 쿼리 생성
                    generated_sql = query_chain.invoke({"dialect" : ChatMyDBClass.engine.dialect,
                                                        "few_shot_question": closest_example["question"],
                                                        "few_shot_sql": closest_example["sql"],
                                                        "table_metadata" : selected_tables,
                                                        "enum_metadata" : ChatMyDBClass.enum_list,
                                                        "question": sql_friendly_question
                                                    })
                    generated_sql_text = text(generated_sql["generated_sql"].replace("\n", " "))
                    print(f"4. Generated SQL Query: {generated_sql_text}")

                    # Step 3: 생성된 SQL 쿼리 표시
                    with st.expander("Step 3: Generated SQL Query", expanded=True):
                        st.code(generated_sql["generated_sql"], language="sql")


                    ################################
                    ## 5. 쿼리검증 및 보정 
                    # 실제 존재하는 테이블, 컬럼으로 구성된 쿼리인지 검증한다.
                    # valid_tables = selected_table_names
                    # valid_columns = obj.extract_colmns_names(selected_tables)
                    # # valid_values = obj.extract_values(valid_cloumns)
                    
                    # validated_query = obj.validate_sql(str(generated_sql_text), valid_tables, valid_columns)
                    
                    # print(f"5. Validated SQL Query: {validated_query}")



                    ################################
                    ## 6. 쿼리 실행
                    sql_result = db_utils.sql_execution(ChatMyDBClass.engine, generated_sql_text)
                    print(f"6. Query_result : {sql_result}")



                    ################################
                    ## 7. 결과 응답 표시
                    # SQL 실행 결과를 세션 상태에 저장
                    if 'query_results' not in st.session_state:
                        st.session_state.sql_result = []  # 쿼리 결과를 저장할 리스트 생성

                    with st.expander("Step 4: SQL Execution Result", expanded=True):
                        if isinstance(sql_result, pd.DataFrame):
                            st.dataframe(sql_result)  # DataFrame 형태로 표시
                        else:
                            st.write(sql_result)  # 에러 메시지 또는 텍스트 출력
                    
                    st_cb = StreamlitCallbackHandler(st.container())
                    
                    # 메시지에 결과 추가
                    st.session_state.messages.append({"role": "assistant", "content": sql_result})

                    # 최종 결과를 채팅 메시지에 표시
                    utils.print_qa(ChatMyDBClass, user_query, sql_result)

                except Exception as e:
                    st.error(f"Failed to process the request: {e}")
        
        



if __name__ == "__main__":
    main()

    