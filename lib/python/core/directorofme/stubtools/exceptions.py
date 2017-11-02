'''
stubtools/orm.py -- exceptions for the stubtools package.

@author: Matt Story <matt@directorof.me>
'''

class StubToolsException(Exception):
    '''Base exception for stubtools'''
    pass

class NotConfiguredError(StubToolsException):
    '''Thrown when a query is not properly configured'''
    pass
