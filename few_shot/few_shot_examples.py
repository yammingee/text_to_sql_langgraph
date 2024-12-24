examples = [
    {
        "question": "현재 기준 진행중인 프로젝트",
        "sql": "SELECT pms_project.name, pms_code.name AS status FROM pms_project JOIN pms_code ON pms_project.status_seq = pms_code.seq WHERE pms_code.name like '%진행%';"
    },
    {
        "question": "A 프로젝트의 금주 실제 진척률과 금주 계획 진척률",
        "sql": "SELECT pms_wbs_statistics.real_rate, pms_wbs_statistics.this_week_plan_rate FROM pms_wbs_statistics JOIN pms_project ON pms_wbs_statistics.project_seq = pms_project.seq WHERE pms_project.name LIKE '%A%';"
    }, 
    {
        "question": "금주 계획 진척율이 낮은 순으로 3개 프로젝트",
        "sql": "SELECT pms_project.name, pms_project.customer_name, pms_project.open_date, pms_wbs_statistics.this_week_plan_rate FROM pms_project JOIN pms_wbs_statistics ON pms_project.seq = pms_wbs_statistics.project_seq ORDER BY pms_wbs_statistics.this_week_plan_rate LIMIT 3;"
    }
]