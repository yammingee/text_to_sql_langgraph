from langchain_core.prompts import PromptTemplate

def get_prompt():
    template = """
    You are an SQL expert. Your task is to generate a correct and executable SQL query based on the user's question, 
    using only the tables and columns provided in the `metadatas` and `schema`.

    **Instructions:**
    1. Use **only** the tables and columns listed in the provided `metadatas`.
    2. Make sure the SQL syntax is **correct and executable**.
    3. The query must be relevant to the **intent** of the user's question.
    4. Handle **data types** correctly (e.g., strings must be enclosed in quotes).
    5. **Return the SQL query as a string** suitable for execution, ensuring no newline characters (`\n`) are included.

    ---
    **Schema:**
    {schema}

    **Relevant Tables and Columns (Metadatas):**
    {metadatas}

    **User Query:**
    {user_query}

    **Generated SQL Query:**
    """
    generator_sql_prompt = PromptTemplate(
       input_variables=["schema", "metadatas", "user_query"], template=template
    )
    return generator_sql_prompt
