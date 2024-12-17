from langchain_core.prompts import PromptTemplate

def get_prompt():

    template = """
    You are a SQL expert. Follow these steps:
    1. Rephrase the user's query to be SQL-friendly without converting it into an SQL statement.
    2. Extract the most important keywords from the rephrased query that can be mapped to columns.
    - Use algorithms such as TF-IDF, RAKE, or noun extraction to identify important keywords. 
    - Ensure the keywords are individual words. 
    3. Identify the most relevant table from the only provided table names. Ensure the most relevant table are individual words.
    Consider the following business terms for context: {terms}
    Available Table Names: {table_names} 

    Original Question: {question}

    One Statement
    Step 1. SQL-friendly Rephrased Question(to English):
    Step 2. Extracted Keyword(comma-separated, excluding proper nouns, max 1):
    Step 3. Most Relevant Table:
    """

    sql_friendly_question_prompt = PromptTemplate(
        input_variables=["terms", "question", "table_names"], template=template
    )

    return sql_friendly_question_prompt
