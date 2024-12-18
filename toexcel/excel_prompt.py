from langchain_core.prompts import PromptTemplate

def get_prompt():
    template = """
    You are an assistant that answers questions based on data extracted from an Excel document. Each row represents a specific record.
    Use the information in the 'context' below to answer the question concisely and accurately.

    Context:
    {context}

    Question:
    {question}

    Answer:
    """

    excel_prompt = PromptTemplate(
        input_variables=["question", "context"], 
        template=template
    )
    return excel_prompt
