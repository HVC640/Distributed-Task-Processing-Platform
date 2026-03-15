from handlers.email_handler import send_email_handler
from handlers.report_handler import report_handler

TASK_HANDLERS = {
    "send_email": send_email_handler,
    "generate_report": report_handler
}