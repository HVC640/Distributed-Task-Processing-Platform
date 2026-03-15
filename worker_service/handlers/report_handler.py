def report_handler(payload):
    # Simulate report generation
    import time
    time.sleep(5)  # Simulate time-consuming task
    return f"Report generated with data: {payload}"