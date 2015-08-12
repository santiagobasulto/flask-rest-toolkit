def get_task_index_by_id(tasks, task_id):
    return ([t['id'] for t in tasks]).index(task_id)


def get_task_by_id(tasks, task_id):
    return tasks[get_task_index_by_id(tasks, task_id)]
