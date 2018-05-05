import functools

from sqlalchemy.event import listen
from slugify import slugify

__all__ = [ "slugify_on_change" ]

def slugify_on_change(src, target, default=True):
    '''Class decorator that slugs an attribute when it changes and stores it to another attribute.
       By default it will automatically initialize the target value as well.

       NB: this does not play well with abstract classes or inheritence, and should only be used by
       concrete models.
    '''
    @functools.wraps(slugify_on_change)
    def inner(cls):
        if not hasattr(cls, "__table__") and not hasattr(cls, "__tablename__"):
            raise ValueError("May not be used with non-concrete models")

        old_init = cls.__init__
        def __init__(self, *args, **kwargs):
            old_init(self, *args, **kwargs)
            src_value = getattr(self, src, None)

            if src_value is not None:
                setattr(self, target, slugify(src_value))

        cls.__init__ = __init__

        listen(getattr(cls, src), "set", lambda obj, v, x, y: setattr(obj, target, slugify(v)))
        return cls

    return inner
