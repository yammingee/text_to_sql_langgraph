from openai import OpenAI
import re
import os

from my_utils import utils as utils
from my_utils import db_utils as db_utils
from sqlalchemy import text


client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY")
)

# query_get_custom_proper_nouns.json 에 설정된 쿼리 기반 고유명사 조회
def getProperNouns(self):
    db_connection = self.db.connect()
    try:
        query_get_proper_nouns = self.proper_nouns_query
        result = {}
        for item in query_get_proper_nouns:
            column_name = item["column_name"]
            query_result = db_utils.sql_execution(self, text(item["sql"]))

            # 특수 문자 제거 및 이름 정리
            cleaned_names = [
                re.sub(r'[\[\]\(\)\"\']', '', name.strip())  # 불필요한 특수 문자 제거
                for name in query_result[column_name].tolist()
            ]
            result[item["type"]] = cleaned_names    
    finally:
        db_connection.close()

    return result


# 사전 고유명사 리스트 기반 검색
def match_proper_nouns_with_user_define_list(user_input, proper_nouns):
    print("사전 고유명사 리스트 기반 검색")
    result = {}
    
    for proper_type, proper_list in proper_nouns.items():
        matches = [proper_noun for proper_noun in proper_list if proper_noun in user_input]
        if matches:
            result[proper_type] = ', '.join(matches)

    if not result:
        return None

    formatted_result = []
    for proper_type, matches in result.items():
        formatted_result.append(f"- {proper_type}: {matches}")

    return '\n'.join(formatted_result)


# GPT NER 작업 지시 - 다중 엔티티 추출 적용
def match_with_gpt(user_input, entity_types):
    print("GPT NER 작업 지시 - 다중 엔티티 추출 적용")
    # 엔티티 유형을 동적으로 시스템 메시지에 전달
    entity_instructions = ", ".join([f"'{entity}'" for entity in entity_types])
    
    response = client.chat.completions.create(
        model= "gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": f"You are a system that extracts the following entities: {entity_instructions} from input text."},
            {"role": "user", "content": f"Extract the entities ({', '.join(entity_types)}) from the following input: {user_input}"}
        ],
        temperature=0
    )

    return response.choices[0].message.content



# 사용자 질의에 따른 엔티티 분류 및 고유 명사 추출 처리
def matched_proper_noun(_self, user_input):

    # query_get_custom_proper_nouns.json 에 설정된 쿼리 기반 고유명사 조회
    proper_nouns = getProperNouns(_self)

    # information_type 데이터 가져오기
    information_type_datas = utils.getInformationTypeDatas()
    merged_proper_nouns = { **proper_nouns, **information_type_datas}

    proper_types = []
    for proper_type, proper_list in merged_proper_nouns.items():
        proper_types.append(proper_type)

    # 리스트 기반 탐색
    list_matched_proper_noun = match_proper_nouns_with_user_define_list(user_input, merged_proper_nouns)
    if list_matched_proper_noun:
        return list_matched_proper_noun

    # GPT API 백업 탐색
    gpt_matched_proper_noun = match_with_gpt(user_input, proper_types)
    return gpt_matched_proper_noun



