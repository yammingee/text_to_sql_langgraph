from langchain_core.prompts import PromptTemplate

def get_prompt():

   template= """
    You are a business and SQL expert. Follow these steps:
    1. Rephrase the user's query to be SQL-friendly.
    2. Extract keywords from the rephrased query that can be mapped to table names.
    Consider the following business terms for context: {terms}

    Original Question: {question}

    Step 1: SQL-friendly Rephrased Question:
    Step 2: Extracted Keywords for Table Mapping:"""

   sql_friendly_question_prompt = PromptTemplate(
      input_variables=["terms", "question"], template=template
   )

   return sql_friendly_question_prompt
