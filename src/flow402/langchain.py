from functools import wraps
from .reporter import Flow402Reporter
import os

reporter = Flow402Reporter(None, api_key=os.getenv("FLOW402_API_KEY"))  # global singleton

def track_tool(api_key: str = None, event_type: str = "spend"):
    """
    Decorator for LangChain tools to track x402 spend.
    @track_tool()
    def my_paid_tool(...):
        ...
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            # Na MVP – użytkownik musi podać dane ręcznie w tool docstring lub kwargs
            # W przyszłości możemy odczytać z kontekstu x402
            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            return result

        return async_wrapper if "__call__" in dir(func) and hasattr(func.__call__, "__code__") else sync_wrapper
    return decorator
