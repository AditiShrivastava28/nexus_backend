"""
API routers package.

This package contains all the FastAPI router modules
for the different API endpoints.
"""


from .auth import router as auth_router
from .me import router as me_router
from .attendance import router as attendance_router
from .team import router as team_router
from .finances import router as finances_router
from .org import router as org_router
from .inbox import router as inbox_router
from .admin import router as admin_router
from .resume import router as resume_router
from .requests import router as requests_router
from .leaves import router as leaves_router
from .employee_logs import router as employee_logs

__all__ = [
    "auth_router",
    "me_router",
    "attendance_router",
    "team_router",
    "finances_router",
    "org_router",
    "inbox_router",
    "admin_router",
    "resume_router",
    "requests_router",
    "leaves_router",
    "employee_logs",
]
