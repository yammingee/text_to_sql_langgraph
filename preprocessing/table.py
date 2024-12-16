from sqlalchemy import MetaData


# 테이블 메타데이터에서 유효값 추출
def get_table_info(engine):
    try:
        metadata = MetaData()
        metadata.reflect(bind=engine)
        table_info = {}

        for table_name, table in metadata.tables.items():
            columns = []
            relationships = []

            # 컬럼 정보와 유효값 추출
            for column in table.columns:
                comment = column.comment if column.comment else "no comment"
                valid_values = extract_valid_values(column)
                columns.append({"name": column.name, "comment": comment, "valid_values": valid_values})
            # 외래 키 관계 추출
            for fk in table.foreign_key_constraints:
                relationships.append({
                    "column": list(fk.columns)[0].name,
                    "referred_table": fk.referred_table.name,
                    "referred_column": list(fk.elements)[0].target_fullname,
                })

            table_info[table_name] = {"columns": columns, "relationships": relationships}
        return table_info
    except Exception as e:
        print(f"Error reflecting metadata: {e}")
        raise

# 테이블 DDL 구조화
def structured_tables(table_info):
    structured_texts = []

    for table_name, details in table_info.items():
        # 각 컬럼 정보 처리: 유효값 포함
        column_descriptions = ", ".join(
            [
                f"{col['name']}: {col['comment']}" + 
                (f" (Valid values: {', '.join(col['valid_values'])})" if col['valid_values'] else "")
                for col in details["columns"]
            ]
        )
        # 외래 키 관계 처리
        if details["relationships"]:
            relationship_descriptions = "\n  ".join(
                [
                    f"Column '{rel['column']}' references '{rel['referred_table']}' (Column: {rel['referred_column']})"
                    for rel in details["relationships"]
                ]
            )
            relationships_text = f"\nRelationships:\n  {relationship_descriptions}"
        else:
            relationships_text = "\nRelationships: None"

        # 테이블과 관련된 정보를 하나의 텍스트로 묶기
        structured_text = (
            f"Table Name: {table_name}\n"
            f"Columns: {column_descriptions}{relationships_text}"
        )
        structured_texts.append(structured_text)

    return structured_texts

# 컬럼에서 유효값 추출 (주석이나 제약조건 기반)
def extract_valid_values(column):
    if column.default:
        # 컬럼의 기본값이 유효값으로 사용될 경우
        return [str(column.default)]
    elif hasattr(column, 'constraints'):
        # CHECK 제약 조건에서 유효값 추출 (예시)
        for constraint in column.constraints:
            if hasattr(constraint, 'sqltext'):
                return [val.strip("'") for val in constraint.sqltext.text.split("IN (")[1].split(")")[0].split(",")]
    return []