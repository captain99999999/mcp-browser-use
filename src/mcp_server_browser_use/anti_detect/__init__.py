"""Anti-detection module for web tools (web_search, web_fetch).

Provides stealth JS injection, Chrome launch arguments, and helper
utilities to reduce the chance of triggering bot-detection systems.
"""

from .stealth import get_chrome_stealth_args, get_stealth_scripts, inject_stealth_scripts

__all__ = ["get_chrome_stealth_args", "get_stealth_scripts", "inject_stealth_scripts"]
