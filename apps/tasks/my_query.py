from django.db import connection

def my_annotate():
    query1 = '''
            CREATE TEMPORARY TABLE work_cal AS
                SELECT tasks_todo_sub_executor.*, tasks_todo.*
                FROM tasks_todo_sub_executor
                INNER JOIN tasks_todo
                    ON tasks_todo_sub_executor.todo_id = tasks_todo.id
                ORDER BY user_id;
             '''
    query2 = '''
            -- 计算每个工作包协办人数量并插入临时表
            UPDATE work_cal SET sub_executor_count = (
                SELECT COUNT(*) FROM tasks_todo_sub_executor
                WHERE work_cal.todo_id = tasks_todo_sub_executor.todo_id);
             '''
    query3 = '''
            SELECT exe_id, SUM(total_pre_work), SUM(total_real_work) FROM
                (
                    -- 承办任务
                    SELECT main_executor_id AS exe_id, SUM(predict_work * evaluate_factor) AS total_pre_work,
                           SUM(real_work * tasks_todo.evaluate_factor) AS total_real_work
                    FROM tasks_todo
                    GROUP BY exe_id
                    UNION ALL
                    -- 协办任务
                    SELECT user_id AS exe_id, SUM(predict_work * (1 -evaluate_factor) / sub_executor_count) AS total_pre_work,
                           SUM(real_work * (1 - evaluate_factor) / sub_executor_count) AS total_real_work
                    FROM work_cal
                    GROUP BY exe_id
                ) AS init
                GROUP BY exe_id  
            '''
    cursor = connection.cursor()
    cursor.execute(query1)
    cursor.execute(query2)
    cursor.execute(query3)
    raw = cursor.fetchall()
    return raw