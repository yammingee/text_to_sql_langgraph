from openai import OpenAI
import re
import os
import json

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
            table_name = item["table_name"]
            query_result = db_utils.sql_execution(self, text(item["sql"]))

            # 특수 문자 제거 및 이름 정리
            cleaned_names = [
                {
                    "column_name": column_name,
                    "table_name": table_name,
                    "proper_noun": re.sub(r'[\[\]\(\)\"\']', '', name.strip())  # 불필요한 특수 문자 제거
                }
                for name in query_result[column_name].tolist()
            ]
            
            # item["type"]에 매칭된 키에 추가
            if item["type"] not in result:
                result[item["type"]] = []  # 초기화
            result[item["type"]].extend(cleaned_names)   
    finally:
        db_connection.close()
    return result


# 사전 고유명사 리스트 기반 검색
def match_proper_nouns_with_user_define_list(user_input, proper_nouns):
    print("사전 고유명사 리스트 기반 검색")
    result = {
        "proper_nouns": [],
        "information_type": []
    }
    for proper_type, proper_list in proper_nouns.items():
        if isinstance(proper_list, list) and isinstance(proper_list[0], dict):
            for item in proper_list:
                if item["proper_noun"] in user_input:
                    result["proper_nouns"].append({
                        "proper_type": proper_type,
                        "column_name": item["column_name"],
                        "table_name": item["table_name"],
                        "proper_noun": item["proper_noun"]
                    })
        else:
            matches = [proper_noun for proper_noun in proper_list if proper_noun in user_input]
            if matches:
                result["information_type"].extend(matches)
    return result if result["proper_nouns"] or result["information_type"] else {}


# GPT NER 작업 지시 - 다중 엔티티 추출 적용
def match_with_gpt(user_input, entity_types, proper_nouns):
    print("GPT NER 작업 지시 - 다중 엔티티 추출 적용 :")
    
    # 고유명사를 사용자 입력에서 매칭
    result = {
        "proper_nouns": [],
        "information_type": []
    }
    for proper_type, proper_list in proper_nouns.items():
        if isinstance(proper_list, list) and isinstance(proper_list[0], dict):
            for item in proper_list:
                if item["proper_noun"] in user_input:
                    result["proper_nouns"].append({
                        "proper_type": proper_type,
                        "column_name": item["column_name"],
                        "table_name": item["table_name"],
                        "proper_noun": item["proper_noun"]
                    })
        else:
            matches = [proper_noun for proper_noun in proper_list if proper_noun in user_input]
            if matches:
                result["information_type"].extend(matches)
    result if result["proper_nouns"] or result["information_type"] else {}

    print(result)

    # GPT 요청 구성
    entity_instructions = ", ".join([f"'{entity}'" for entity in entity_types])

    gpt_prompt = (
        f"You are a system that extracts entities and infers missing information types based on the following entity types: {entity_instructions}. "
        "If no proper nouns are explicitly found, include an empty proper_nouns array in the output. "
        "For information types, infer the intent from the input even if the information type is not explicitly mentioned. "
        "For example, if the user asks for a 'task', include 'task' in the information_type."
        "\n\nOutput the result in JSON format as follows: "
        "{'proper_nouns': [{'proper_type': 'entity_type', 'column_name': 'column_name', 'table_name': 'table_name', 'proper_noun': 'extracted_value'}], "
        "'information_type': ['extracted_value', ...]}. "
        "\n\nIf no entities or information types are found, return an empty JSON object: {}."
    )

    gpt_response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": gpt_prompt},
            {"role": "user",
             "content": (
                 f"Based on the input: '{user_input}', extract relevant entities ({entity_instructions}) and infer any missing information types."
             )
            }
        ],
        temperature=0
    )

    # GPT 결과 받아오기
    gpt_result = gpt_response.choices[0].message.content.replace("'", "\"")
    gpt_parsed_result = json.loads(gpt_result)

    # proper_nouns 결과를 GPT 추론 결과와 병합
    final_result = {
        "proper_nouns": result.get("proper_nouns", []),
        "information_type": gpt_parsed_result.get("information_type", [])
    }

    return final_result


# 사용자 질의에 따른 엔티티 분류 및 고유 명사 추출 처리
def matched_proper_noun(_self, user_input):

    # query_get_custom_proper_nouns.json 에 설정된 쿼리 기반 고유명사 조회
    proper_nouns = getProperNouns(_self)

    # information_type 데이터 가져오기
    information_type_datas = utils.getInformationTypeDatas()
    merged_proper_nouns = { **proper_nouns, **information_type_datas}

    proper_types = list(merged_proper_nouns.keys())

    # 리스트 기반 탐색
    list_matched_proper_noun = match_proper_nouns_with_user_define_list(user_input, merged_proper_nouns)
    if list_matched_proper_noun.get('proper_nouns') and list_matched_proper_noun.get('information_type'):
        return list_matched_proper_noun

    # GPT API 백업 탐색
    gpt_matched_proper_noun = match_with_gpt(user_input, proper_types, merged_proper_nouns)
    return gpt_matched_proper_noun



