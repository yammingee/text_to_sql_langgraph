from langchain_core.prompts import PromptTemplate

def get_prompt():
    template = """
        Use the following few-shot example, table metadata, and enum metadata to generate an accurate SQL query.  
        Given an input question, create a syntactically correct {dialect} query to run.

        --- Few-shot Example ---
        Example Question: {few_shot_question}
        Example SQL: {few_shot_sql}

        --- Table Metadata ---
        {table_metadata}

        --- Enum Metadata ---
        {enum_metadata}

        Now, based on the above metadata and the relationships between the tables, generate a SQL query for the following question:
        {question}

        **Important:** 
        - Use the **few-shot SQL example as a reference** to understand structure and patterns, but do not copy it directly. Adapt the query to fit the specific user question.
        - Ensure the query exclusively utilizes the **tables and columns listed in the metadata**.  
        - Only use columns that are explicitly present in the corresponding tables to avoid errors. When specifying JOIN conditions, use only columns that exist in the relevant tables. For example, to JOIN db_service and db_server tables, use db_service.id and db_server.service_id.
        - **The SQL query must explicitly reflect the key terms or metrics mentioned in the user's question.** For example, if the question asks for "backup success rate," the query must include a calculation for `(successful backups / total backups) * 100`.
        - When filtering or applying conditions, **only use the conditions specified in the user’s question**.
        - **Only perform the necessary JOINs** required to retrieve the relevant data for the question. Avoid unnecessary joins.
        - If the question involves the `ha_type` column from the `db_service` table, ensure the filter uses one of these values: `'SINGLE', 'REPLICATION', 'CLUSTER'`.
        - Similarly, for the `backup_status` column in `db_backup_schedule`, valid values are `'DELETED', 'DEACTIVATED', 'ACTIVATED'`, but do not apply any filtering based on this column unless mentioned in the question.
        - **Do not use any values that are not listed in the enum metadata** for that column.  
        - **Do not use the column `use_flag`** in any part of the query.  
        - Apply appropriate **JOIN conditions** only where required based on the metadata’s relationships.
        - **Ensure the query does not contain any Markdown syntax**, such as ` ```sql ` blocks, and return only the plain SQL code.
    """


    generator_sql_prompt = PromptTemplate(
        input_variables=["dialect", "few_shot_question", "few_shot_sql", "table_metadata", "enum_metadata", "question"], 
        template=template
    )
    return generator_sql_prompt
