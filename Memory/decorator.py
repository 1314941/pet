from datetime import datetime

#装饰器
def log_task(func):
    def wrapper(*args, **kwargs):
        start_time = datetime.now()
        print(f"开始执行任务: {func.__name__} - {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        try:
            result = func(*args, **kwargs)
            end_time = datetime.now()
            print(f"任务完成: {func.__name__} - {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"任务耗时: {(end_time - start_time).total_seconds()}秒")
            return result
        except Exception as e:
            print(f"任务异常: {func.__name__} - {str(e)}")
            raise  # 重新抛出异常以供上层处理
    return wrapper

