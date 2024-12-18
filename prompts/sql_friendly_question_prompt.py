from langchain_core.prompts import PromptTemplate

def get_prompt():

    template = """
    You are a SQL expert. Follow these steps:
    1. Rephrase the user's query to make it SQL-friendly without converting it into an SQL statement.
    - Preserve the user's original intent, including key phrases or compound terms (e.g., "current week progress rate").
    - Avoid simplifying or breaking down compound terms if they represent the user's primary intent.
    2. Extract the single most important phrase from the rephrased query that best captures the user's primary intent.
    - If the user's question includes specific phrases like "current week progress rate," extract the entire phrase as-is.
    - Use contextual understanding and provided business terms to ensure accurate and complete extraction.
    3. Identify the single most relevant table name from the provided table names based on the extracted phrase.
    - The table name must be one of the provided names and should be selected with the highest relevance to the extracted phrase.
    - Select the table most likely to contain data related to the extracted phrase.
    Consider the following business terms for context: {terms}
    Available Table Names: {table_names}

    Original Question: {question}

    One Statement
    Step 1. SQL-friendly Rephrased Question:
    Step 2. Extracted Phrase:
    Step 3. Most Relevant Table:
    """

    sql_friendly_question_prompt = PromptTemplate(
        input_variables=["terms", "question", "table_names"], template=template
    )

    return sql_friendly_question_prompt
