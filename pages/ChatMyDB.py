import streamlit as st
import pandas as pd
import numpy as np
import os

from my_utils import utils as utils
from my_utils import db_utils as db_utils
from embeddings import embeddings
from preprocessing import table_info as preProcessedTableData
from langchain.schema.runnable import RunnableMap
from langchain_community.utilities import SQLDatabase
from langchain_core.output_parsers import StrOutputParser
from sqlalchemy import text
from prompts import sql_friendly_question_prompt
from prompts import generator_sql_prompt
from prompts import response_prompt

st.set_page_config(page_title="ChatSQL", page_icon="🛢")
st.header('Chat MyDB 💬')

class ChatMyDBClass:

    def __init__(self):
        utils.sync_st_session()

    def initialize(self):
        try:
            # LLM 설정
            self.llm = utils.configure_llm()
            print("init 1/7 - LLM 설정 완료")

            # DB 연결
            self.db = utils.configure_db('USE_DBAAS_DB')
            self.engine = SQLDatabase(self.db)
            print("init 2/7 - 데이터베이스 연동 완료")

            # 테이블 메타 정보 처리 (제외된 테이블을 고려하여 메타 정보 구성)
            excluded_tables = utils.getExcludedTabls()
            usable_table_names = self.engine.get_usable_table_names()
            self.filtered_table_names = [name for name in usable_table_names if name not in excluded_tables]

            self.table_names_documents = preProcessedTableData.to_document(self.filtered_table_names)
            all_table_info = preProcessedTableData.get_table_info(self.db)

            self.filtered_all_table_info = {
                table_name: info
                for table_name, info in all_table_info.items()
                if table_name not in excluded_tables
            }

            self.filtered_structured_all_table_info = preProcessedTableData.structured_tables(self.filtered_all_table_info)
            self.all_table_info_documents = preProcessedTableData.to_document(self.filtered_structured_all_table_info)
            print("init 3/7 - 메타 정보 전처리 완료")

            # FAISS 벡터 저장소 로드 또는 생성
            faiss_table_names_file_path = "./vectorstore/faiss/table_names"
            faiss_all_talbe_info_file_path = "./vectorstore/faiss/all_table_info"

            if not os.path.exists(faiss_table_names_file_path):
                self.vectorstore_table_names = embeddings.preprocessing(self.table_names_documents, faiss_table_names_file_path)
                self.vectorstore_all_table_info = embeddings.preprocessing(self.all_table_info_documents, faiss_all_talbe_info_file_path)
                print("init 4/7 - FAISS 생성 및 저장 완료")
            else:
                self.vectorstore_table_names = embeddings.load_vectorstore(faiss_table_names_file_path)
                self.vectorstore_all_table_info = embeddings.load_vectorstore(faiss_all_talbe_info_file_path)
                print("init 4/7 - 로컬 FAISS 로드 완료")

            # 비즈니스 용어 사전 로드
            self.terms_list = utils.getBusinessTerm()
            print("init 5/7 - 비즈니스 용어 사전 로드 완료")

            # Few-shot 예제 로드
            self.few_shot_examples = utils.getFewShotExamples()
            print("init 6/7 - Few-shot 예제 로드 완료")

            # Enum 데이터 로드
            self.enum_list = utils.getEnumDatas()
            print("init 7/7 - Enum 데이터 로드 완료")

        except Exception as e:
            st.error(f"초기화 중 오류가 발생했습니다: {e}")


    def process_user_query(self, user_query):

        try:
            # Step 1: 질문을 SQL-friendly 하게 변환, 관련 테이블 추출 - LLM
            print(f"====Step 1: 질문을 SQL-friendly 하게 변환, 관련 테이블 추출===")

            chain = RunnableMap({"output": sql_friendly_question_prompt.get_prompt() | self.llm | StrOutputParser()})
            result = chain.invoke({"question": user_query,
                                    "terms": self.terms_list,
                                    "table_names": self.filtered_table_names})

            output_content = result["output"]
            output_lines = [line for line in output_content.split("\n") if line.strip()]

            sql_friendly_question = output_lines[0].split(":", 1)[1].strip()
            top_keywords = output_lines[1].split(":", 1)[1].strip()
            top_relevant_table = output_lines[2].split(":", 1)[1].strip()
            
            with st.expander("1. SQL-friendly Question:", expanded=True):
                st.code(output_content)

            print(f"1-1. SQL-friendly Question: {sql_friendly_question}")
            print(f"1-2. Extracted Keywords for Table Mapping: {top_keywords}")
            print(f"1-3. Most Relevant Table: {top_relevant_table}")


            # Step 2: 연관 테이블 및 컬럼 정보 - RAG 로 메타정보에서 찾기
            print(f"============Step 2: 연관 테이블 및 컬럼 정보 RAG============")

            extracted_relevant_tables = []

            # keyword 로 관련 테이블 찾기 
            retriever = self.vectorstore_all_table_info.as_retriever(search_kwargs={'k':2})
            docs = retriever.invoke(top_keywords)
            page_contents = [doc.page_content for doc in docs]
            extracted_top_relevant_table_by_kewords = db_utils.extract_table_names(page_contents[0].strip())
            extracted_relevant_tables.append(extracted_top_relevant_table_by_kewords)
            print(f"2-1. Relevant_table: {extracted_top_relevant_table_by_kewords}")

            # relevant_table 로 관련 테이블 찾기
            retriever = self.vectorstore_table_names.as_retriever(search_kwargs={'k': 1})
            docs = retriever.invoke(top_relevant_table)
            page_contents = [doc.page_content for doc in docs]
            extracted_relevant_table_by_table_name = page_contents[0].strip()
            extracted_relevant_tables.append(extracted_relevant_table_by_table_name)

            print(f"2-2. Extracted_top_relevant_tables: {extracted_relevant_table_by_table_name}")
            print(f"2-3. Total_relevant_tables: {extracted_relevant_tables}")
            
            # relevant_table 의 연관관계 테이블 가져오기
            expanded_tables = db_utils.expand_with_foreign_keys(extracted_relevant_tables, self.filtered_structured_all_table_info)
            rephrased_embedding = embeddings.generate_embeddings([extracted_relevant_table_by_table_name])
            print(f"2-4. Final Selected Tables: {expanded_tables}")
            
            with st.expander("Step 2: Selected Tables", expanded=True):
                st.write(expanded_tables)
        
            
            # 연관 테이블의 컬럼, 연관관계 정보만 가져오기
            extracted_top_relevant_table_info = []

            for item in self.filtered_structured_all_table_info:
                for table_name in expanded_tables:
                    if "Table Name: " + table_name + "\n" in item:
                        extracted_top_relevant_table_info.append(item)
    

            # Step 3: Few-shot 예제 검색 및 적용 - RAG
            print(f"============Step 3: Few-shot 예제 검색 및 적용- RAG============")
            example_embeddings = embeddings.generate_embeddings([ex["question"] for ex in self.few_shot_examples])
            few_shot_example_index = embeddings.create_faiss_index(example_embeddings) 
            distances, indices = few_shot_example_index.search(np.array(rephrased_embedding), 1)
            closest_example = self.few_shot_examples[indices[0][0]]
            print(f"3. Selected Few-shot Example: {closest_example}")

            with st.expander("Step 3: Selected Few-shot Example", expanded=True):
                st.code(closest_example, language="sql")



            # Step 4: SQL 쿼리 생성
            print(f"============Step 4: SQL 쿼리 생성 ============")
            query_chain = RunnableMap({"generated_sql": generator_sql_prompt.get_prompt() | self.llm})
            result = query_chain.invoke({
                "dialect": self.engine.dialect,
                "few_shot_question": closest_example["question"],
                "few_shot_sql": closest_example["sql"],
                "top_relevant_table" : extracted_relevant_tables,
                "table_metadata": extracted_top_relevant_table_info, 
                "enum_metadata": self.enum_list,
                "question": user_query
            })
            generated_sql = result["generated_sql"].content
            print(f"4. Generated SQL: {generated_sql}")

            with st.expander("Step 4: Generated SQL Query", expanded=True):
                st.code(generated_sql, language="sql")


            # Step 5: SQL 실행 및 응답 생성
            print(f"============Step 5: SQL 실행 ============")
            sql_result = db_utils.sql_execution(self, text(generated_sql))
            print(f"5. SQL Execution Result: {sql_result}")

            with st.expander("Step 5: SQL Execution Result", expanded=True):
                if isinstance(sql_result, pd.DataFrame):
                    st.dataframe(sql_result)
                else:
                    st.write(sql_result)
        

            # Step 6: LLM을 활용한 자연어 응답 생성
            print(f"====Step 6: Generate Natural Language Response ===")
            response_chain = RunnableMap({"response": response_prompt.get_prompt() | self.llm})
            result = response_chain.invoke({
                "user_query": user_query,
                "generated_sql": generated_sql,
                "sql_result": sql_result
            })
            response = result["response"].content
            print(f"6. Generate Natural Language Response: {response}")

            with st.expander("Step 6: Assistant's Response", expanded=True):
                st.write(response)
                st.dataframe(sql_result)

            return response

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
                st.info('\n- ' + '\n- '.join(self.filtered_table_names))

        # 사용자 입력 처리
        user_query = st.chat_input(placeholder="Ask me anything!")

        if user_query:
            st.session_state.messages.append({"role": "user", "content": user_query})
            st.chat_message("user").write(user_query)

            with st.chat_message("assistant"):
                with st.spinner("답변을 생성 중입니다..."):
                    response = self.process_user_query(user_query)
                    st.session_state.messages.append({"role": "assistant", "content": str(response)})
                        






# 클래스 인스턴스를 st.session_state에 저장하여 상태 유지
if "chat_my_db_instance" not in st.session_state:
    st.session_state["chat_my_db_instance"] = ChatMyDBClass()

chat_my_db_instance = st.session_state["chat_my_db_instance"]

# 앱 실행
chat_my_db_instance.main()
