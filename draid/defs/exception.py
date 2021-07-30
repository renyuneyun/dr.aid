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


class OntologyException(Exception):
    '''
    The base exception class for any ontology-related exceptions
    '''
    pass


class OntologyTypeException(OntologyException):
    '''
    The type of the fetched entry is different from expected.
    '''
    pass


class ForceFailedException(Exception):
    '''
    An exception representing that a "force" action (i.e. trying to ensure something) failed. It often indicates the data is different from expectation.
    '''
    pass

class ParseError(Exception):
    '''
    Parsing procedure encounteres an unexpected item. Probably the data is ill-formed.
    '''
    pass
