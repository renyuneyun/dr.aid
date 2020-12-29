'''
Custom Exceptions
'''

class IllegalStateError(RuntimeError):
    pass

class IllegalCaseError(IllegalStateError):
    '''
    An exception representing that possible cases should have been exausted, and this case should not be reached.
    '''
    pass
