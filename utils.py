from time import perf_counter
from functools import wraps
def timeit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = perf_counter()
        result = func(*args, **kwargs)
        end = perf_counter()
        print(f"Time Elapsed ({func.__name__}): {end-start:.4f} s")
        return result
    return wrapper
class TimeitMeta(type):
    """
    実行時間計測のためのラッパー
    実行時間のボトルネックを探すときに使う
    同じクラスの関数を複数回呼ぶ場合、計測と表示のオーバーヘッドが加わるので不正確になる
    """
    def __new__(meta, class_name, bases, class_attrs):
        new_attrs = {}
        for name, val in class_attrs.items():
            new_attrs[name] = timeit(val) if callable(val) else val
        return type(class_name, bases, new_attrs)