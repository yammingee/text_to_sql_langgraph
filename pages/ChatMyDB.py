import streamlit as st
import pandas as pd
import numpy as np
import os

from my_utils import utils as utils
from my_utils import db_utils as db_utils
from rag import preprocessing as RagPreProcessing
from data_processing import table_info as PreProcessedTableData
from data_processing import proper_nouns as ProcessingProperNounData
from langchain.schema.runnable import RunnableMap
from langchain_community.utilities import SQLDatabase
from langchain_core.output_parsers import StrOutputParser
from sqlalchemy import text

from prompts import sql_friendly_question_prompt
from prompts import generator_sql_prompt
from few_shot import example_selector as few_shot_selector
from prompts import response_prompt

st.set_page_config(page_title="ChatSQL", page_icon="🛢")
st.header('Chat MyDB 💬')

faiss_table_names_file_path = "./vectorstore/faiss/table_names"
faiss_all_talbe_info_file_path = "./vectorstore/faiss/all_table_info"
faiss_few_shot_file_path = "./vectorstore/faiss/faiss_few_shot"

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

            # 테이블 메타 정보 전처리 (제외된 테이블을 고려하여 메타 정보 구성)
            excluded_tables = utils.getExcludedTabls()
            usable_table_names = self.engine.get_usable_table_names()
            self.filtered_table_names = [name for name in usable_table_names if name not in excluded_tables]

            self.table_names_documents = PreProcessedTableData.to_document(self.filtered_table_names)
            all_table_info = PreProcessedTableData.get_table_info(self.db)

            self.filtered_all_table_info = {
                table_name: info
                for table_name, info in all_table_info.items()
                if table_name not in excluded_tables
            }

            self.filtered_structured_all_table_info = PreProcessedTableData.structured_tables(self.filtered_all_table_info)
            self.all_table_info_documents = PreProcessedTableData.to_document(self.filtered_structured_all_table_info)
            print("init 3/7 - 메타 정보 전처리 완료")

            # FAISS 벡터 저장소 로드 또는 생성
            if not os.path.exists(faiss_table_names_file_path):
                self.vectorstore_table_names = RagPreProcessing.to_vectorstore_from_documents(self.table_names_documents, faiss_table_names_file_path)
                self.vectorstore_all_table_info = RagPreProcessing.to_vectorstore_from_documents(self.all_table_info_documents, faiss_all_talbe_info_file_path)
                print("init 4/7 - FAISS 생성 및 저장 완료")
            else:
                self.vectorstore_table_names = RagPreProcessing.load_vectorstore(faiss_table_names_file_path)
                self.vectorstore_all_table_info = RagPreProcessing.load_vectorstore(faiss_all_talbe_info_file_path)
                print("init 4/7 - 로컬 FAISS 로드 완료")

            # 고유 명사 추출 쿼리 설정 로드
            self.proper_nouns_query = utils.getProperNouns()
            print("init 5/7 - 고유 명사 추출 쿼리 설정 로드 완료")

            # 비즈니스 용어 사전 로드
            self.terms_list = utils.getBusinessTerm()
            print("init 6/7 - 비즈니스 용어 사전 로드 완료")

            # Enum 데이터 로드
            self.enum_list = utils.getEnumDatas()
            print("init 7/7 - Enum 데이터 로드 완료")

        except Exception as e:
            st.error(f"초기화 중 오류가 발생했습니다: {e}")


    def process_user_query(self, user_query):

        try:
            print(f"====Step 1. 사용자 질문 분석 : NER 및 Embedding 기반 고유명사/키워드 추출===")
            # 1-1 ~ 1-2. 고유 명사 및 핵심 키워드 추출
            matched_merged_proper_nouns = ProcessingProperNounData.matched_proper_noun(self, user_query)
            matched_proper_nouns = []
            matched_information_type = []

            for proper_noun in matched_merged_proper_nouns.get('proper_nouns', []):
                matched_proper_nouns.append(proper_noun)

            for info_type in matched_merged_proper_nouns.get('information_type', []):
                matched_information_type.append(info_type)

            print(f"1-1. Proper nouns From Question: {matched_proper_nouns}")
            print(f"1-2. Keyword: {matched_information_type}")

            print(f"====Step 2. 관련 테이블 검색: 벡터 검색 및 유사도 기반 테이블/컬럼 매핑===")

            print(f"====Step 3. 질문 재구성: GPT 및 규칙 기반 SQL-friendly 문장 생성===")
            chain = RunnableMap({"output": sql_friendly_question_prompt.get_prompt() | self.llm | StrOutputParser()})
            result = chain.invoke({"question": user_query,
                                    "proper_nouns" : matched_proper_nouns,
                                    "information_types" : matched_information_type,
                                    "terms": self.terms_list,
                                    "meta_table_names": self.filtered_table_names})

            output_content = result["output"]
            output_lines = [line for line in output_content.split("\n") if line.strip()]
            top_relevant_table = output_lines[0].split(":", 1)[1].strip()
            sql_friendly_question = output_lines[1].split(":", 1)[1].strip()
            top_relevant_table_array = [item.strip() for item in top_relevant_table.split(",")]
            if(proper_noun):
                top_relevant_table_array.append(proper_noun["table_name"])
            print(top_relevant_table_array)

            print(f"1-3. Most Relevant Table: {top_relevant_table}")
            print(f"1-4. SQL-friendly Question: {sql_friendly_question}")

            with st.expander("Step 1: Rephrased User Question:", expanded=True):
                st.code(output_content)


            # Step 2: 연관 테이블 및 컬럼 정보 - RAG 로 메타정보에서 찾기
            print(f"====Step 4. 테이블 검증: RAG를 통해 테이블/컬럼 존재 여부와 메타정보 확인===")

            extracted_relevant_tables = []

            # 2-1. relevant_table 로 관련 실제 테이블 찾기 (RAG)
            for top_relevant_table in top_relevant_table_array:
                retriever = self.vectorstore_table_names.as_retriever(search_kwargs={'k': 1, 'distance_metric': 'cosine'})
                docs = retriever.invoke(top_relevant_table)
                page_contents = [doc.page_content for doc in docs]
                extracted_relevant_table_by_table_name = page_contents[0].strip()
                extracted_relevant_tables.append(extracted_relevant_table_by_table_name)

            print(f"2-1. Relevant_table: {extracted_relevant_tables}")
            
            # 2-2. relevant_table 의 연관관계 테이블 가져오기
            expanded_tables = db_utils.expand_with_foreign_keys(extracted_relevant_tables, self.filtered_structured_all_table_info)
            print(f"2-2. Final Selected Tables: {expanded_tables}")
            
            # 2-3. 연관 테이블의 컬럼, 연관관계 정보만 가져오기
            extracted_top_relevant_table_info = db_utils.expanded_tables(self, extracted_relevant_tables)
            print(f"2-3. Relationship Informations: {extracted_top_relevant_table_info}")

            with st.expander("Step 2: Selected Tables", expanded=True):
                st.write(expanded_tables)


            # Step 3: Few-shot 예제 프롬프트 적용 및 SQL 쿼리 생성
            print(f"============ Step 5. Few-shot 예제 강화: 클러스터링 기반 다양한 문맥 반영 ============")
            selected_example = few_shot_selector.example_selector.select_examples({"question" : sql_friendly_question})[0]
            print(f"3. Selected Examples: {selected_example}")
            with st.expander("Step 3: Selected Few-shot Example", expanded=True):
                st.code(selected_example, language="json")

    
            # Step 4: SQL 쿼리 생성
            print(f"============ Step 6. SQL 생성: 쿼리 최적화 및 실행 가능성 검증 ============")
            query_chain = RunnableMap({"generated_sql": generator_sql_prompt.get_prompt() | self.llm})
            result = query_chain.invoke({
                "dialect": self.engine.dialect,
                "few_shot_question": selected_example["question"],
                "few_shot_sql": selected_example["sql"],
                "top_relevant_tables" : expanded_tables,
                "table_metadata": extracted_top_relevant_table_info, 
                "enum_metadata": self.enum_list,
                "question": sql_friendly_question,
                "proper_nouns" : matched_proper_nouns,
                "information_type" : matched_information_type
            })
            generated_sql_queries = result["generated_sql"].content.split(";")
            print(f"4. Generated SQL: {generated_sql_queries}")

            with st.expander("Step 4: Generated SQL Query", expanded=True):
                for i, query in enumerate(generated_sql_queries):
                    if query.strip():  # 쿼리가 비어있지 않은 경우만 출력
                        st.code(query.strip(), language="sql")


            # Step 5: SQL 실행 및 응답 생성
            print(f"============Step 5: SQL 실행 ============")
            sql_results = []
            for query in generated_sql_queries:
                if query.strip():  # 쿼리가 비어있지 않은 경우 실행
                    sql_result = db_utils.sql_execution(self, text(query.strip()))
                    sql_results.append(sql_result)
                    print(f"Executed SQL: {query.strip()}")
                    print(f"Execution Result: {sql_result}")

            with st.expander("Step 5: SQL Execution Results", expanded=True):
                for i, result in enumerate(sql_results):
                    if isinstance(result, pd.DataFrame):
                        st.write(f"Result for Query {i+1}:")
                        st.dataframe(result)
                    else:
                        st.write(f"Result for Query {i+1}: {result}")
        
            # Step 6: LLM을 활용한 자연어 응답 생성
            print(f"====Step 6: Generate Natural Language Response ===")
            response_chain = RunnableMap({"response": response_prompt.get_prompt() | self.llm})
            result = response_chain.invoke({
                "user_query": user_query,
                "generated_sql": ";\n".join(generated_sql_queries),  # 모든 쿼리를 하나의 문자열로 전달
                "sql_result": sql_results
            })
            response = result["response"].content
            print(f"6. Generate Natural Language Response: {response}")

            with st.expander("Step 6: Assistant's Response", expanded=True):
                st.write(response)
                for result in sql_results:
                    if isinstance(result, pd.DataFrame):
                        st.dataframe(result)
                    else:
                        st.write(result)

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
                    ########## TO-DO 사용자 의도 분석 모듈 추가
                    response = self.process_user_query(user_query)
                    st.session_state.messages.append({"role": "assistant", "content": str(response)})
                        






# 클래스 인스턴스를 st.session_state에 저장하여 상태 유지
if "chat_my_db_instance" not in st.session_state:
    st.session_state["chat_my_db_instance"] = ChatMyDBClass()

chat_my_db_instance = st.session_state["chat_my_db_instance"]

# 앱 실행
chat_my_db_instance.main()
