from langchain_core.prompts import PromptTemplate

def get_prompt():

    from langchain_core.prompts import PromptTemplate

def get_prompt():
    template = """
        다음의 few-shot 예제, 테이블 메타데이터, 열거형 메타데이터, 가장 관련성 높은 테이블, 고유명사, 키워드 를 참고하여 정확한 SQL 쿼리를 생성하세요.  
        입력된 질문에 따라 실행할 수 있는 {dialect} SQL 쿼리를 작성하세요.

        --- Few-shot 예제 ---
        예제 질문: {few_shot_question}
        예제 SQL: {few_shot_sql}

        --- 가장 관련성 높은 테이블 ---
        질문과 관련성이 가장 높은 테이블: {top_relevant_tables}

        --- 테이블 메타데이터 ---
        {table_metadata}

        --- 열거형 메타데이터 ---
        {enum_metadata}

        --- 고유명사 ---
        {proper_nouns}

        --- 키워드 ---
        {information_type}

        이제 위의 메타데이터와 테이블 간의 관계를 기반으로 다음 질문에 대한 SQL 쿼리를 생성하세요:
        {question}

       **중요:** 
        - 쿼리에서 **테이블 메타데이터({table_metadata})에 나열된 테이블과 열만 사용**하세요.  
        - **가장 관련성 높은 테이블({top_relevant_tables})**을 쿼리의 시작점으로 사용하세요.
        - {top_relevant_tables}에 대한 관계가 {table_metadata}에 정의되어 있다면:
            1. 관계 메타데이터에 따라 참조 정보(Relationships)가 정의된 경우:
                - 정의된 모든 참조된 테이블과 열을 JOIN하여 값을 가져오세요.
                - JOIN 조건은 참조된 외래 키(`foreign_key_column`)와 기본 키(`primary_key_column`)의 관계에 따라 올바르게 지정하세요 (예: `foreign_key_column = primary_key_column`).
            2. JOIN의 우선순위는 질문과 관련된 핵심 테이블({top_relevant_tables})에서 시작하며, 그 다음으로 참조된 테이블로 확장됩니다.
            3. 동일한 테이블을 여러 번 JOIN해야 할 경우 충돌을 방지하기 위해 **테이블 별칭(e.g., `table_name AS alias`)**을 사용하세요.
        - SELECT 문에서 **질문에 필요한 데이터 열만 명시적으로 포함**하세요. 
          - 질문에 명시적으로 언급되지 않았지만, 관계 메타데이터에서 필수적으로 요구되는 열은 쿼리에 포함하세요.
        - `SELECT *`는 불필요한 데이터 검색을 방지하기 위해 사용하지 마세요. 필요한 열만 명시적으로 포함하세요.
        - 동일한 테이블이 여러 용도로 사용될 경우(e.g., pms_code가 다른 용도로 사용되는 경우) 각 인스턴스에 의미 있는 별칭(e.g., `pms_code AS type_code`, `pms_code AS phase_code`)을 부여하고, SELECT 및 JOIN 절에서 열을 적절히 참조하세요.
        - WHERE 절에 컬럼이 name 인 경우, **`=` 대신 `LIKE` 절을 사용**하세요. 
          - `LIKE` 절을 사용할 때는 적절한 와일드카드 문자(`%`)를 추가하여 검색 조건을 유연하게 처리하세요.
        - **열거형 메타데이터에 나열되지 않은 값은 쿼리에서 사용하지 마세요.**  
        - **few-shot SQL 예제를 참조**하여 구조와 패턴을 이해하되, 이를 그대로 복사하지 마세요. 사용자 질문에 맞게 쿼리를 조정하세요.
        - **쿼리에는 Markdown 문법(예: ` ```sql `)을 포함하지 말고**, 순수한 SQL 코드만 반환하세요.

    """

    generator_sql_prompt = PromptTemplate(
        input_variables=["dialect", "table_metadata", "enum_metadata", "question", "top_relevant_tables", "proper_nouns", "information_type", "few_shot_question", "few_shot_sql"], 
        template=template
    )
    return generator_sql_prompt

