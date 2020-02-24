from threading import Thread
from functools import wraps
import wx


def in_new_thread(target_func):
    """Wrapper to execute function in new thread"""
    @wraps(target_func)
    def wrapper(*args, **kwargs):
        com_thread = Thread(target=target_func, args=args, kwargs=kwargs)
        com_thread.start()
    return wrapper


def in_main_thread(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        wx.CallAfter(func, *args, **kwargs)

    return wrapper
