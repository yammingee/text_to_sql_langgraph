from langchain_core.prompts import PromptTemplate

def get_prompt():

    template = """
    User asked: {user_query}
    Generated SQL: {generated_sql}
    SQL Execution Result: {sql_result}
    
    Generate a concise and clear natural language response for the user, ensuring the response is in the same language as the user's question.

    """

    sql_friendly_question_prompt = PromptTemplate(
        input_variables=["user_query", "generated_sql", "sql_result"], template=template
    )

    return sql_friendly_question_prompt
