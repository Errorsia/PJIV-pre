class RequireNameMixin:
    required_methods = ["set_page_name"]

    def __init_subclass__(cls):
        super().__init_subclass__()
        for method in cls.required_methods:
            if not hasattr(cls, method):
                raise TypeError(f"{cls.__name__} must implement {method}()")