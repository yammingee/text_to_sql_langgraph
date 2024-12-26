from langchain_core.prompts import PromptTemplate

def get_prompt():
    template = """
    프롬프트:
        - 사용자는 SQL 전문가이며, SQL 쿼리를 작성하는 데 필요한 정보를 제공합니다.
        - 입력 변수 {proper_nouns}은 고유명사의 목록으로, 각 고유명사는 다음과 같은 정보로 구성됩니다:
            - proper_type: 고유명사의 유형
            - proper_noun: 고유명사 값
            - column_name (proper_nouns_column_name): 관련된 데이터베이스 테이블의 컬럼 이름
            - table_name (proper_nouns_table_name): 고유명사가 포함된 테이블 이름
        - 입력 변수 {information_types}은 SQL 쿼리에서 조회하고자 하는 핵심 키워드들의 목록입니다.
        - 입력 변수 {meta_table_names} 테이블 이름 배열 입니다.
        - top_relevant_table 을 선택할 때, 다음 조건을 따르세요:
            1. {proper_nouns}이 포함되어 있다면, 고유명사와 관련된 테이블인 proper_nouns_table_name(고유명사의 테이블 이름)을 top_relevant_table에 포함시켜 반환해야 합니다. 
            2. {information_types} 이 포함되어 있다면, 각 핵심 키워드에 대해 {meta_table_names}에서 가장 관련성 높은 하나의 테이블만 (top_relevant_table)을 선택해야 합니다. 핵심 키워드와 테이블 간의 연관성은 의미적으로 결정됩니다.
        - {question}을 SQL 쿼리 형식에 맞게 변환한 (converted_question) 을 생성할 때, 다음 조건을 따르세요:
            1. 변환된 질문(converted_question)은 원 질문({question})의 모든 세부 사항과 뉘앙스를 반영해야 합니다.
            2. 사용자가 명시한 요구사항, 조건, 또는 맥락을 빠짐없이 포함시켜야 합니다.
            3. 변환된 질문은 가장 관련성 높은 테이블(top_relevant_table)과 연결되어야 합니다.
            4. 질문에 포함된 시간, 상태, 또는 기타 맥락적 요소(예: "현재 기준", "지난 1주일", "완료된" 등)는 변환된 질문에 반드시 포함해야 합니다.
            - 변환된 사용자 질문은 다음 조건에 따라 생성되어야 합니다:
                1. {proper_nouns}이 값이 존재하는 경우:
                    - table_name (proper_nouns_table_name), column_name (proper_nouns_column_name), proper_noun, information_types, top_relevant_table
                2. {proper_nouns}이 값이 존재하지 않는 경우:
                    - information_types, top_relevant_table"
        - top_relevant_table과 converted_question 값을 반환하세요. (입력 예시나 값은 포함하지 않습니다.)

    """

    sql_friendly_question_prompt = PromptTemplate(
        input_variables=["terms", "question", "meta_table_names", "proper_nouns", "information_types"], template=template
    )

    return sql_friendly_question_prompt
