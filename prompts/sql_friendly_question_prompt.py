from langchain_core.prompts import PromptTemplate

def get_prompt():
    template = """
    프롬프트 설명:
        - 사용자는 SQL 전문가이며, SQL 쿼리를 작성하기 위해 필요한 정보를 제공합니다.
        - {question} 에서 추출한 의도에 맞게 SQL 쿼리를 작성합니다.
        - 입력 변수 {proper_nouns}은 고유명사의 목록이며, 각 고유명사는 다음과 같은 정보로 구성됩니다:
            - proper_type: 고유명사의 유형
            - column_name: 관련된 데이터베이스 테이블에서의 컬럼 이름
            - table_name: 해당 고유명사가 포함된 테이블 이름
            - proper_noun: 실제 고유명사 값
        - {information_types}은 추출해야 할 핵심 키워드들의 목록입니다. 각 핵심 키워드는 SQL 쿼리에서 조회하고자 하는 정보를 나타냅니다.
        - 사용자 질문을 바탕으로 고유명사와 핵심 키워드를 연결하여, 해당 키워드에 적합한 테이블과 컬럼을 찾아 SQL 쿼리를 작성합니다.
        - 각 핵심 키워드에 대해 {meta_table_names}에서 가장 관련성 높은 **하나의 테이블만** 선택해야 합니다. 핵심 키워드와 테이블 간의 매핑은 의미적 연관성에 기반하여 결정됩니다. 

    출력 형식:
        - {proper_nouns} 와 {information_types} 가 모두 존재하면:
            - 출력 형식을 모두 반환하도록 하세요.
        - {proper_nouns}가 비어 있고, {information_types} 이 비어 있지 않으면:
            - 고유명사와 고유명사와 관련된 테이블 정보는 None으로 설정하고, 핵심 키워드는 반드시 반환하도록 하고, 변환된 사용자 질문에서 조회 조건을 생략합니다.
        - {proper_nouns}가 비어 있지 않고, {information_types}이 비어 있으면:
            - 핵심 키워드는 None으로 설정합니다. 변환된 사용자 질문에서 조회 조건을 반드시 포함하도록 합니다.
        - {proper_nouns}과 {information_types}이 모두 비어 있으면:
            - 고유명사, 고유명사와 관련된 테이블 정보, 핵심 키워드는 모두 None으로 설정합니다.
        - {proper_nouns}, {information_types} 입력값이 모두 비어 있으면, 출력 형식의 변환된 사용자 질문은 주어진 {question}을 참고하여 선택합니다.

    조건에 맞는 출력 형식만 반환하도록 다음의 항목을 작성하세요:

    1. 고유명사: "proper_noun" (고유명사가 있을 경우, 리스트를 문자열로 변환하여 출력)
    2. 고유명사와 관련된 테이블 정보: table_name, column_name (고유명사와 관련된 테이블 및 컬럼이 있을 경우 출력)
    3. 핵심 키워드: "information_types" (핵심 키워드가 있을 경우, 리스트를 문자열로 변환하여 출력)
    4. 가장 연관성 높은 테이블: top_relevant_table (핵심 키워드에 가장 관련성 높은 테이블을 출력)
    5. 변환된 사용자 질문: converted_question

    출력 형식 예시:
        1. 고유명사: "마트 해외 IT 고도화 리뉴얼 프로젝트"
        2. 고유명사와 관련된 테이블 정보: pms_project, name
        3. 핵심 키워드: "회의록", "투입인력"
        4. 가장 연관성 높은 테이블: pms_meeting_minute, pms_input_person
        5. 변환된 사용자 질문: "pms_meeting_minute 테이블에서 '회의록' 정보를 조회해주세요. 조회 조건은 pms_project 테이블에서 name 이 '마트 해외 IT 고도화 리뉴얼 프로젝트' 프로젝트 입니다.", "pms_input_person 테이블에서 '투입인력' 정보를 조회해주세요. 조회 조건은 pms_project 테이블에서 name 이 '마트 해외 IT 고도화 리뉴얼 프로젝트' 프로젝트 입니다."
    """

    sql_friendly_question_prompt = PromptTemplate(
        input_variables=["terms", "question", "meta_table_names", "proper_nouns", "information_types"], template=template
    )

    return sql_friendly_question_prompt
