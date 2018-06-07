import contextlib

import flask
from . import groups, exceptions

__all__ = [ "RequiresDecorator", "group", "scope", "feature", "admin", "staff", "everybody", "anybody", "push" ]

class RequiresDecorator(contextlib.ContextDecorator):
    def __init__(self, group_or_requirement, and_=None, or_=None, session=flask.session):
        self.group = group_or_requirement if isinstance(group_or_requirement, groups.Group) else None
        self.requirement = group_or_requirement if isinstance(group_or_requirement, RequiresDecorator) else None

        if self.group is None and self.requirement is None:
            raise ValueError("Must pass a group or requirement, not {}".format(type(group_or_requirement)))

        self.and_requires = and_ if and_ is None or isinstance(and_, RequiresDecorator) \
                                 else RequiresDecorator(and_)
        self.or_requires = or_ if or_ is None or isinstance(or_, RequiresDecorator) \
                               else RequiresDecorator(or_)
        self.session = session
        super().__init__()

    def __enter__(self):
        '''Support with scoping for permissioning, not really a context, but syntactically it works nicely'''
        if not self.test():
            raise exceptions.PermissionDeniedError(self)
        return self

    def __exit__(self, *args):
        '''No-op, required by context protocol'''
        pass

    def __and__(self, other):
        return RequiresDecorator(self, and_=other)

    def __or__(self, other):
        return RequiresDecorator(self, or_=other)

    def test(self):
        groups_test = self.group and self.group in self.session.groups
        requirements_test = self.requirement and self.requirement.test()

        if not groups_test and not requirements_test:
            if not (self.or_requires and self.or_requires.test()):
                return False

        return not self.and_requires or self.and_requires.test()

    def and_(self, other):
        return self.__and__(other)

    def or_(self, other):
        return self.__or__(other)

### Porcelin
def group(group):
    return RequiresDecorator(group)

def scope(name, perm_name):
    return group(groups.Scope(display_name=name, __perms__={perm_name}).perms[perm_name])

def feature(name):
    return group(groups.Group(display_name=name, type=groups.GroupTypes.feature))

push = group(groups.push)
user = group(groups.user)
admin = group(groups.admin)
staff = group(groups.staff)
everybody = anybody = group(groups.everybody)
