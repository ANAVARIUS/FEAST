import builtins
import logging

def _forbidden_print(*args, **kwargs):
    pass

#builtins.print = _forbidden_print