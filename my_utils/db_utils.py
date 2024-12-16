import pandas as pd

# 테이블 이름 추출
def extract_table_names(selected_tables):
    # 각 테이블 정보 문자열에서 'Table Name: ' 뒤에 나오는 이름만 추출
    table_names = [
        table.split('\n')[0].replace('Table Name: ', '').strip()
        for table in selected_tables
    ]
    return table_names

# 컬럼 이름 추출
def extract_colmns_names(selected_tables):
    # 각 테이블 정보 문자열에서 'Columns: ' 뒤에 나오는 이름만 추출
    column_names = [
        table.split('\n')[0].replace('Columns: ', '').strip()
        for table in selected_tables
    ]
    print(f"extract_colmns_names: {column_names}")
    return column_names


# 쿼리 실행
def sql_execution(_self, inputs):
    try:
        with _self.db.connect() as connection:
            result = connection.execute(inputs)
            rows = result.fetchall()  # 모든 결과 가져오기
            columns = result.keys()  # 컬럼명 가져오기
            # 중복된 컬럼명 처리
            unique_columns = []
            for col in columns:
                if col in unique_columns:
                    # 중복된 컬럼명을 처리하여 별칭 추가
                    count = unique_columns.count(col) + 1
                    unique_columns.append(f"{col}_{count}")
                else:
                    unique_columns.append(col)

            # 결과를 DataFrame으로 변환
            df = pd.DataFrame(rows, columns=unique_columns)
            return df  # DataFrame 반환
    except Exception as e:
        return f"SQL execution failed: {e}"


# 사용자 질의와 테이블 컬럼 및 이름을 기준으로 필터링
def filter_relevant_tables(query, selected_table_names, threshold=0.5):
    relevant_tables = []
    # 질의의 키워드 추출
    query_keywords = set(query.lower().split())    
    for table_name in selected_table_names:
        # 테이블 이름과 질의 키워드 교집합이 존재하는지 확인
        if query_keywords & set(table_name.split()):
            relevant_tables.append(table_name)
    print(query_keywords)
    return relevant_tables


# 외래키로 연결된 추가 테이블 포함
def expand_with_foreign_keys(relevant_tables, all_tables):
    expanded_tables = set(relevant_tables)
    for table in relevant_tables:
        for rel in table.get("relationships", []):
            referred_table_name = rel["referred_table"]
            referred_table = next(
                (t for t in all_tables if t["name"] == referred_table_name), None
            )
            if referred_table:
                expanded_tables.add(referred_table)
    return list(expanded_tables)


# 쿼리 검증 (테이블, 컬럼 및 유효값 검증 포함)
def validate_sql(sql_query, valid_tables, valid_columns):
    missing_tables = []
    missing_columns = []
    invalid_values = []

    # 테이블 검증
    for table in valid_tables:
        if table.lower() not in sql_query.lower():
            missing_tables.append(table)
    # 컬럼 및 유효값 검증
    for column_info in valid_columns:
        column_name = column_info['name']
        if column_name.lower() not in sql_query.lower():
            missing_columns.append(column_name)
        # 유효값 검증
        valid_values = column_info.get('valid_values', [])
        if valid_values:
            # 쿼리에서 해당 컬럼의 유효값을 사용했는지 검증
            if not any(f"'{value}'" in sql_query for value in valid_values):
                invalid_values.append((column_name, valid_values))

    # 검증 실패 시 에러 메시지 생성
    error_messages = []
    if missing_tables:
        error_messages.append(f"Missing tables: {', '.join(missing_tables)}")
    if missing_columns:
        error_messages.append(f"Missing columns: {', '.join(missing_columns)}")
    if invalid_values:
        for column, values in invalid_values:
            error_messages.append(f"Invalid value for column '{column}': Expected one of {values}")

    # 에러가 있다면 예외 발생
    if error_messages:
        raise ValueError("SQL Validation Error:\n" + "\n".join(error_messages))
    # 검증 성공 시 쿼리 반환
    return sql_query