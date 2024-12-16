import streamlit as st
import pandas as pd
import numpy as np
import faiss
import os

from my_utils import utils as utils
from my_utils import db_utils as db_utils
from embeddings import embeddings
from preprocessing import table as preProcessedTableData
from prompts import rag_prompt as rag_prompt
from prompts import generator_sql_prompt as generator_sql_prompt
from langchain_community.callbacks import StreamlitCallbackHandler
from langchain.schema.runnable import RunnableMap
from langchain_community.utilities import SQLDatabase

from sqlalchemy import text
from prompts import sql_friendly_question_prompt
from prompts import generator_sql_with_few_shot_prompt

st.set_page_config(page_title="ChatSQL", page_icon="🛢")
st.header('Chat MyDB 💬')

class ChatMyDBClass:

    def __init__(self):
        utils.sync_st_session()

    def initialize(self):
        try:
            # LLM 설정
            self.llm = utils.configure_llm()
            print("1/7 - LLM 설정 완료")

            # DB 연결
            self.db = utils.configure_db('USE_DBAAS_DB')
            self.engine = SQLDatabase(self.db)
            print("2/7 - 데이터베이스 연동 완료")

            # 테이블 메타 정보 처리
            self.table_info = preProcessedTableData.get_table_info(self.db)
            self.structured_table_info_texts = preProcessedTableData.structured_tables(self.table_info)
            print("3/7 - 테이블 구조화 완료")

            # FAISS 벡터 저장소 로드 또는 생성
            faiss_file_path = "faiss_index.idx"
            if not os.path.exists(faiss_file_path):
                meta_data_embedding = embeddings.generate_embeddings(self.structured_table_info_texts)
                self.meta_data_faiss_index = embeddings.create_faiss_index(meta_data_embedding)
                faiss.write_index(self.meta_data_faiss_index, faiss_file_path)
                print("4/7 - 벡터 저장소 생성 및 저장 완료")
            else:
                self.meta_data_faiss_index = faiss.read_index(faiss_file_path)
                print("4/7 - FAISS 인덱스 로드 완료")

            # 비즈니스 용어 사전 로드
            self.terms_list = utils.getBusinessTerm()
            print("5/7 - 비즈니스 용어 사전 로드 완료")

            # Few-shot 예제 로드
            self.few_shot_examples = utils.getFewShotExamples()
            print("6/7 - Few-shot 예제 로드 완료")

            # Enum 데이터 로드
            self.enum_list = utils.getEnumDatas()
            print("7/7 - Enum 데이터 로드 완료")

        except Exception as e:
            st.error(f"초기화 중 오류가 발생했습니다: {e}")


    def process_user_query(self, user_query):
        try:
            # Step 1: 질문을 SQL-friendly하게 변환
            chain = RunnableMap({"sql_friendly_question": sql_friendly_question_prompt.get_prompt() | self.llm})
            result = chain.invoke({"question": user_query, "terms": self.terms_list})
            sql_friendly_question = result["sql_friendly_question"].content
            print(f"1. SQL-friendly Question & Keyword for Table Mapping : {sql_friendly_question}")

            with st.expander("1. SQL-friendly Question & Keyword for Table Mapping", expanded=True):
                st.code(sql_friendly_question)

            # Step 2: 관련 테이블 및 컬럼 정보 검색
            rephrased_embedding = embeddings.generate_embeddings([sql_friendly_question])
            distances, indices = embeddings.search_faiss_index(self.meta_data_faiss_index, rephrased_embedding)
            selected_tables = [self.structured_table_info_texts[i] for i in indices]
            selected_table_names = db_utils.extract_table_names(selected_tables)
            print(f"2. Selected Tables: {selected_table_names}")

            with st.expander("Step 2: Selected Tables", expanded=True):
                st.write(selected_table_names)

            # Step 3: Few-shot 예제 검색 및 적용
            example_embeddings = embeddings.generate_embeddings([ex["question"] for ex in self.few_shot_examples])
            few_shot_example_index = embeddings.create_faiss_index(example_embeddings)
            distances, indices = few_shot_example_index.search(np.array(rephrased_embedding), 1)
            closest_example = self.few_shot_examples[indices[0][0]]
            print(f"3. Selected Few-shot Example: {closest_example}")

            # Step 4: SQL 쿼리 생성
            query_chain = RunnableMap({"generated_sql": generator_sql_with_few_shot_prompt.get_prompt() | self.llm})
            result = query_chain.invoke({
                "dialect": self.engine.dialect,
                "few_shot_question": closest_example["question"],
                "few_shot_sql": closest_example["sql"],
                "table_metadata": selected_tables,
                "enum_metadata": self.enum_list,
                "question": sql_friendly_question
            })
            generated_sql = result["generated_sql"].content
            print(f"4. Generated SQL: {generated_sql}")

            with st.expander("Step 3: Generated SQL Query", expanded=True):
                st.code(generated_sql, language="sql")

            # Step 5: SQL 실행
            sql_result = db_utils.sql_execution(self, text(generated_sql))
            print(f"5. SQL Execution Result: {sql_result}")

            with st.expander("Step 4: SQL Execution Result", expanded=True):
                if isinstance(sql_result, pd.DataFrame):
                    st.dataframe(sql_result)
                else:
                    st.write(sql_result)

            return sql_result

        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
            return None


    @utils.enable_chat_history
    def main(self):
        # session state 초기화
        if not st.session_state.get("initialized"):
            print("Initializing application...")
            self.initialize()
            st.session_state["initialized"] = True

        print("Main execution started")

        # 사이드바에서 데이터베이스 옵션 선택
        st.sidebar.title("Database Options")
        radio_opt = ['Use My db - MySQL (wepljec)']
        selected_opt = st.sidebar.radio(
            label='Choose Database',
            options=radio_opt
        )

        db_uri = 'USE_DBAAS_DB' if radio_opt.index(selected_opt) == 0 else None

        if not db_uri:
            st.error("Please enter database URI to continue!")
            return

        if self.engine._engine.connect:
            with st.sidebar.expander('Database tables', expanded=True):
                st.info('\n- ' + '\n- '.join(self.engine.get_usable_table_names()))

        # 사용자 입력 처리
        user_query = st.chat_input(placeholder="Ask me anything!")

        if user_query:
            st.session_state.messages.append({"role": "user", "content": user_query})
            st.chat_message("user").write(user_query)

            with st.chat_message("assistant"):
                with st.spinner("답변을 생성 중입니다..."):
                    sql_result = self.process_user_query(user_query)
                    st.session_state.messages.append({"role": "assistant", "content": str(sql_result)})
                        






# 클래스 인스턴스를 st.session_state에 저장하여 상태 유지
if "chat_my_db_instance" not in st.session_state:
    st.session_state["chat_my_db_instance"] = ChatMyDBClass()

chat_my_db_instance = st.session_state["chat_my_db_instance"]

# 앱 실행
chat_my_db_instance.main()
