from langchain_core.prompts import PromptTemplate

def get_prompt():

    template = """
    프롬프트:
        - 사용자는 SQL 전문가입니다.
        - 사용자 질문의 의도는 {terms} 를 참고하도록 하세요.
        - 입력 변수인 `{proper_nouns}`에서 `INFORMATION_TYPE`의 값이 None이 아닌 경우 이를 "핵심 키워드"로 취급하세요.
        - 입력 변수인 `{proper_nouns}`에서 `INFORMATION_TYPE`을 제외한 타입의 값은 사용자가 정의한 고유명사로 간주합니다. INFORMATION_TYPE 은 고유명사가 될 수 없습니다.
        - 입력 변수인 `{proper_nouns}`에서 "타입이름 : 값" 으로 입력됩니다. "타입이름"은 영문 입력값을 직관적으로 번역하세요.
        - 변환된 사용자 질문은 고유명사를 "타입이름"과 "값"으로 표현하고, 핵심 키워드를 명시하여 다음 형식으로 작성하세요:
            변환된 사용자 질문 형식 : "타입이름"이(가) "값"에 대한 "핵심 키워드" 정보를 조회해주세요.
        - 테이블 선택 시, "핵심 키워드"들을 참고하여 {table_names} 에서 가장 관련성 높은 테이블을 결정합니다.

    출력 예시:
        1. 고유명사:
        2. 핵심 키워드:
        3. 변환된 사용자 질문:
        4. 가장 연관성 높은 테이블: 
    """

    sql_friendly_question_prompt = PromptTemplate(
        input_variables=["terms", "question", "table_names", "proper_nouns"], template=template
    )

    return sql_friendly_question_prompt
