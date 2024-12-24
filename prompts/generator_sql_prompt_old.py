from langchain_core.prompts import PromptTemplate

def get_prompt():
    template = """
        Use the following few-shot example, table metadata, and enum metadata to generate an accurate SQL query.  
        Given an input question, create a syntactically correct {dialect} query to run.

        --- Few-shot Example ---
        Example Question: {few_shot_question}
        Example SQL: {few_shot_sql}

        --- Top Relevant Table ---
        The top relevant table based on the question is: {top_relevant_table}

        --- Table Metadata ---
        {table_metadata}

        --- Enum Metadata ---
        {enum_metadata}

        Now, based on the above metadata and the relationships between the tables, generate a SQL query for the following question:
        {question}

       **Important:** 
        - Ensure the query exclusively utilizes the **tables and columns listed in the metadata ({table_metadata})**.  
        - Use the **top relevant table ({top_relevant_table})** as the starting point for the query.
        - If relationships are defined in the metadata for {top_relevant_table}:
            - Identify all tables related to {top_relevant_table} based on the relationships defined in the metadata.
            - Join all these related tables to {top_relevant_table}.
            - **Use table aliases (e.g., `table_name AS alias`)** when the same table is joined multiple times to avoid conflicts.
            - Ensure JOIN conditions are correctly specified using the relationship definitions in the metadata (e.g., `foreign_key_column = primary_key_column`).
        - **Include all the columns defined in the Relationships metadata** in the SELECT statement. Ensure that columns defined in relationships are included in the query, even if they aren't explicitly mentioned in the question.
        - Avoid using `SELECT *` to limit unnecessary data retrieval. Instead, explicitly include only the columns needed from the related tables.
        - If the same table is used multiple times (e.g., pms_code for different purposes), assign each instance a meaningful alias (e.g., `pms_code AS type_code`, `pms_code AS phase_code`) and reference the columns accordingly in the SELECT and JOIN clauses.
        - Ensure that the query includes all the data from the {top_relevant_table} and its directly related tables as defined by the relationships.
        - **Do not use any values that are not listed in the enum metadata** for that column.  
        - Use the **few-shot SQL example as a reference** to understand structure and patterns, but do not copy it directly. Adapt the query to fit the specific user question.
        - **Ensure the query does not contain any Markdown syntax**, such as ` ```sql ` blocks, and return only the plain SQL code.

    """

    generator_sql_prompt = PromptTemplate(
        input_variables=["dialect", "few_shot_question", "few_shot_sql", "table_metadata", "enum_metadata", "question", "top_relevant_table"], 
        template=template
    )
    return generator_sql_prompt
