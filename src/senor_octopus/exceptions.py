"""
Exceptions for Señor Octopus.
"""


class SenorOctopusException(Exception):
    """
    Base class for all Señor Octopus exceptions.
    """


class InvalidConfigurationException(SenorOctopusException):
    """
    Raised when the configuration YAML is invalid.
    """
