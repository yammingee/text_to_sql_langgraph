from langchain_core.prompts import PromptTemplate

def get_prompt():
    template = """
    You are an expert in analyzing database schemas and metadata. 
    Your task is to identify **relevant tables, columns, and their relationships** based on the user's query, 
    using the **comments** associated with each column for context.

    **Instructions:**
    1. Analyze the provided `context` and `schema` to find the **most relevant tables and columns** based on the user's query.
    2. Focus on the **column comments** to determine relevance to the user's question.
    3. Include **foreign key relationships** or any **relevant joins** between tables when applicable, ensuring to list all tables involved in the joins.
    4. If a column has **comments**, include them in the output.
    5. If no relevant tables, columns, or relationships are found, respond with:  
    `'No relevant tables, columns, or relationships found.'`

    ---
    **Context (Relevant Document Embeddings):**
    {context}

    **Database Schema:**
    {schema}

    **User Query:**
    {user_query}

    **Format your response as follows:**

    - **Table Name**: <table_name>
        - **Columns**:
            - <column_name>: <column_comment> (only include relevant columns)
        - **Relationships** (if any):
            - <relationship_description> (include all join details)

    **Example:**
    - **Table Name**: employees
        - **Columns**:
            - id: Employee ID (if relevant)
            - name: Employee Name (if relevant)
            - salary: Employee Salary (if relevant)
            - department_id: Department ID (if relevant)
        - **Relationships**:
            - employees.department_id -> departments.dept_id
            - departments.dept_id -> projects.department_id (if applicable)

    **If no relevant data is found, respond exactly with:**  
    `'No relevant tables, columns, or relationships found.'`
    """

    metadata_prompt = PromptTemplate(
        input_variables=["context", "user_query", "schema"], template=template
    )
    return metadata_prompt
