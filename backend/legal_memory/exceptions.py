"""
Custom exceptions for Legal Memory Tool
"""

class LegalMemoryError(Exception):
    """Base exception for Legal Memory Tool"""
    pass

class SeleniumError(LegalMemoryError):
    """Error with Selenium operations"""
    pass

class WebsiteBlockedError(LegalMemoryError):
    """Website blocked our request"""
    pass

class SearchError(LegalMemoryError):
    """Error during legal search"""
    pass

class ContractAnalysisError(LegalMemoryError):
    """Error during contract analysis"""
    pass

class KeywordExtractionError(LegalMemoryError):
    """Error during keyword extraction"""
    pass

class RateLimitError(LegalMemoryError):
    """Rate limit exceeded"""
    pass

class ConfigurationError(LegalMemoryError):
    """Configuration error"""
    pass