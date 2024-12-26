from langchain.chains import GraphChain
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI
from langchain.schema import BaseRunnable

# SQL 쿼리 생성 노드
class SQLQueryNode(BaseRunnable):
    def invoke(self, inputs):
        # 사용자 질문에 맞는 SQL 쿼리 생성
        question = inputs['question']
        if "진척율" in question:
            sql_query = "SELECT project_name, progress_rate, status FROM projects WHERE status = '금주 상황';"
        elif "A 프로젝트의 B 사람의 지난주, 이번주 한일" in question:
            sql_query = "SELECT task, date FROM tasks WHERE project_name = 'A 프로젝트' AND person_name = 'B 사람' AND (date BETWEEN '2023-12-18' AND '2023-12-24' OR date BETWEEN '2023-12-25' AND '2023-12-31');"
        return {'sql_query': sql_query}

# SQL 쿼리 실행 노드
class ExecuteSQLNode(BaseRunnable):
    def __init__(self, db_connection):
        self.db_connection = db_connection

    def invoke(self, inputs):
        # SQL 쿼리 실행
        sql_query = inputs['sql_query']
        result = self.db_connection.execute(sql_query)
        return {'sql_result': result}

# 주간보고서 생성 노드
class ReportGenerationNode(BaseRunnable):
    def invoke(self, inputs):
        # SQL 결과를 바탕으로 주간보고서 생성
        result = inputs['sql_result']
        report = f"주간보고서:\n{result}"
        return {'report': report}

# LangGraph 연결
class WeeklyReportGraph(GraphChain):
    def __init__(self, db_connection):
        query_node = SQLQueryNode()
        execute_node = ExecuteSQLNode(db_connection)
        report_node = ReportGenerationNode()

        super().__init__(nodes=[query_node, execute_node, report_node], edges=[
            (query_node, execute_node),  # SQL 쿼리 실행
            (execute_node, report_node)   # 주간보고서 작성
        ])

# DB 연결 예시
class MockDBConnection:
    def execute(self, query):
        # 임시 DB 결과
        if "진척율" in query:
            return [{"project_name": "A 프로젝트", "progress_rate": "80%", "status": "금주 진행 중"}]
        elif "A 프로젝트" in query:
            return [{"task": "Task 1", "date": "2023-12-18"}, {"task": "Task 2", "date": "2023-12-22"}]

# 사용 예시
def main():
    db_connection = MockDBConnection()  # 실제 DB 연결로 대체
    graph = WeeklyReportGraph(db_connection)

    # 사용자 입력 예시
    user_query_1 = "진척율은 그래프로 삽입해주고 금주 상황에 대해 요약해서 주간보고 작성해줘"
    result_1 = graph.invoke({'question': user_query_1})
    print(result_1['report'])

    user_query_2 = "A 프로젝트의 B 사람의 지난주, 이번주 한일에 대해 요약해줘"
    result_2 = graph.invoke({'question': user_query_2})
    print(result_2['report'])

if __name__ == "__main__":
    main()
