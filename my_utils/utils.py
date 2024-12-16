
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

# # GPT-4o-mini 설정
# gpt4o_mini = ChatOpenAI(
#     model_name="gpt-4o-mini",  # GPT-4o-mini에 해당하는 모델명
#     temperature=0.7,
#     max_tokens=150,
# )

# # GPT-4o 설정
# gpt4o = ChatOpenAI(
#     model_name="gpt-4o",  # GPT-4o에 해당하는 모델명
#     temperature=0.7,
#     max_tokens=300,
# )


import os
import getpass
import json
import streamlit as st
import sqlite3
import urllib.parse
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine

from streamlit.logger import get_logger
from langchain_openai import ChatOpenAI
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_community.utilities import SQLDatabase

logger = get_logger('Langchain-Chatbot')

if not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = getpass.getpass()

#decorator
def enable_chat_history(func):
    if os.environ.get("OPENAI_API_KEY"):

        # to clear chat history after swtching chatbot
        current_page = func.__qualname__
        if "current_page" not in st.session_state:
            st.session_state["current_page"] = current_page
        if st.session_state["current_page"] != current_page:
            try:
                st.cache_resource.clear()
                del st.session_state["current_page"]
                del st.session_state["messages"]
            except:
                pass

        # to show chat history on ui
        if "messages" not in st.session_state:
            st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]
        for msg in st.session_state["messages"]:
            st.chat_message(msg["role"]).write(msg["content"])

        # Ensure session state initialization
        if "initialized" not in st.session_state:
            st.session_state["initialized"] = False


    def execute(*args, **kwargs):
        func(*args, **kwargs)
    return execute

#decorator
def enable_chat_history_for_docs(func):
    if os.environ.get("OPENAI_API_KEY"):

        # to clear chat history after swtching chatbot
        current_page = func.__qualname__
        if "current_page" not in st.session_state:
            st.session_state["current_page"] = current_page
        if st.session_state["current_page"] != current_page:
            try:
                st.cache_resource.clear()
                del st.session_state["current_page"]
                del st.session_state["messages"]
            except:
                pass

        # to show chat history on ui
        if "messages" not in st.session_state:
            st.session_state["messages"] = [{"role": "assistant", "content": "파일을 업로드해주세요."}]
        for msg in st.session_state["messages"]:
            st.chat_message(msg["role"]).write(msg["content"])

    def execute(*args, **kwargs):
        func(*args, **kwargs)
    return execute


def display_msg(msg, author):
    """Method to display message on the UI

    Args:
        msg (str): message to display
        author (str): author of the message -user/assistant
    """
    st.session_state.messages.append({"role": author, "content": msg})
    st.chat_message(author).write(msg)

def configure_llm():
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)    
    return llm

def print_qa(cls, question, answer):
    log_str = "\nUsecase: {}\nQuestion: {}\nAnswer: {}\n" + "------"*10
    logger.info(log_str.format(cls.__name__, question, answer))

@st.cache_resource
def configure_embedding_model():
    embedding_model = FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")
    return embedding_model

def sync_st_session():
    for k, v in st.session_state.items():
        st.session_state[k] = v

# DB 연결
def configure_db(db_uri):

    if db_uri == 'USE_SAMPLE_DB':
        # 현재 파일의 부모 디렉토리의 부모 디렉토리 아래에 있는 assets/Chinook.db 파일의 절대 경로
        db_filepath = (Path(__file__).parent.parent / "assets/Chinnok.db").absolute()
        # 현재 파일의 부모 디렉토리의 부모 디렉토리 아래에 있는 assets/Chinook.db 파일의 상대 경로
        # db_filepath = Path(__file__).parent.parent / "assets/Chinnok.db"
        # sqlite:/// 상대 경로 연결 / ////면 절대 경로 연결
        db_uri = f"sqlite:////{db_filepath}"
        creator = lambda: sqlite3.connect(f"file:{db_filepath}?mode=ro", uri=True)
        db = create_engine("sqlite:///", creator=creator)

    if db_uri == 'USE_DBAAS_DB':
        DATABASE_USER = 'root'
        DATABASE_PASSWORD = urllib.parse.quote_plus('ldcc!2626')   #비밀번호 인코딩
        DATABASE_HOST = '127.0.0.1'
        DATABASE_PORT = '3306'
        DATABASE_NAME = 'localpms'
        db_uri = f"mysql+pymysql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
        db = create_engine(db_uri) # 원본 엔진 반환

    return db

def getBusinessTerm():
    filepath = Path(__file__).parent.parent / "assets/business_term.csv"
    df = pd.read_csv(filepath, delimiter=',')
    terms_list = ", ".join([f"{row['terms']}: {row['definition']}" for _, row in df.iterrows()])
    return terms_list


def getFewShotExamples():
    file_path = Path(__file__).parent.parent / "assets/few_shot_examples.json"
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)
    
def getEnumDatas():
    # enum 데이터 추출
    filepath = Path(__file__).parent.parent / "assets/metadata.csv"
    enum_metadata = pd.read_csv(filepath, delimiter=',')
    enum_list = ", ".join([f"{row['column']}: {row['valid_values']}" for _, row in enum_metadata.iterrows()])
    return enum_list


