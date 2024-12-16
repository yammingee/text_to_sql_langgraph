from langchain_core.prompts import PromptTemplate

def get_prompt():

   template= """
    You are a business and SQL expert. Rephrase the user's query to be SQL-friendly.
    Consider the following business terms for context: {terms}

    Original Question: {question}

    SQL-friendly Rephrased Question:"""

   sql_friendly_question_prompt = PromptTemplate(
      input_variables=["terms", "question"], template=template
   )

   return sql_friendly_question_prompt
