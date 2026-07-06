"""ResponseParser - transforms AIResponse into WebsiteProject.

This module re-exports the ResponseParser from the parsers/ subdirectory
for backward compatibility with existing imports.
"""

from app.services.website_generator.parsers.response_parser import ResponseParser

__all__ = ["ResponseParser"]
