"""Anti-detection stealth scripts for web_search and web_fetch tools.

This module provides JavaScript payload and Chrome launch arguments to reduce
bot-detection likelihood when using web tools. Scripts are injected via
browser-use's CDP addScriptToEvaluateOnNewDocument API.

NOTE: This is NOT a dependency-heavy approach. Since browser-use 0.11 dropped
Playwright, we extract the JS payload ourselves rather than using
playwright-stealth or undetected-playwright packages.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from browser_use.browser.session import BrowserSession

logger = logging.getLogger(__name__)


# =============================================================================
# JavaScript Stealth Payloads
# =============================================================================

STEALTH_WEBDRIVER_OVERRIDE: str = r"""
// 1. Override navigator.webdriver to hide automation flag
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined
});
"""

STEALTH_CHROME_RUNTIME_MOCK: str = r"""
// 2. Mock chrome.runtime object for bot detection checks
if (typeof window.chrome === 'undefined') {
    window.chrome = {};
}
if (typeof window.chrome.runtime === 'undefined') {
    window.chrome.runtime = {
        onMessage: { addListener: function() {}, removeListener: function() {} },
        sendMessage: function() {}
    };
}
"""

STEALTH_PERMISSIONS_QUERY_MOCK: str = r"""
// 3. Mock navigator.permissions.query for notification API checks
const originalQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (parameters) => (
    parameters.name === 'notifications' ?
        Promise.resolve({ state: Notification.permission }) :
        originalQuery(parameters)
);
"""

STEALTH_WEBGL_FINGERPRINT_NOISE: str = r"""
// 4. Add noise to WebGL fingerprint (GPU vendor/renderer strings)
const getParameter = WebGLRenderingContext.prototype.getParameter;
WebGLRenderingContext.prototype.getParameter = function(parameter) {
    if (parameter === 37445) {
        return 'Intel Inc.';
    }
    if (parameter === 37446) {
        return 'Intel Iris OpenGL Engine';
    }
    return getParameter.call(this, parameter);
};
"""

STEALTH_CANVAS_FINGERPRINT_NOISE: str = r"""
// 5. Add minimal noise to canvas fingerprinting
const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
HTMLCanvasElement.prototype.toDataURL = function(type) {
    if (type === 'image/png') {
        const canvas = this;
        const ctx = canvas.getContext('2d');
        if (ctx) {
            try {
                const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                for (let i = 0; i < imageData.data.length; i += 4) {
                    imageData.data[i] ^= (Math.random() * 2) | 0;
                    imageData.data[i + 1] ^= (Math.random() * 2) | 0;
                    imageData.data[i + 2] ^= (Math.random() * 2) | 0;
                }
                ctx.putImageData(imageData, 0, 0);
            } catch (e) {
                // Ignore CORS or other errors
            }
        }
    }
    return originalToDataURL.call(this, type);
};
"""


def get_stealth_scripts() -> str:
    """Return all stealth JavaScript payloads as a single concatenated string.

    Includes:
      - navigator.webdriver override
      - chrome.runtime mock
      - navigator.permissions.query mock
      - WebGL fingerprint noise
      - Canvas fingerprint noise
    """
    return "\n".join(
        [
            STEALTH_WEBDRIVER_OVERRIDE,
            STEALTH_CHROME_RUNTIME_MOCK,
            STEALTH_PERMISSIONS_QUERY_MOCK,
            STEALTH_WEBGL_FINGERPRINT_NOISE,
            STEALTH_CANVAS_FINGERPRINT_NOISE,
        ]
    )


def get_chrome_stealth_args() -> list[str]:
    """Return Chrome launch arguments that reduce bot detection likelihood.

    These flags disable automation-related Blink features and security sandbox
    restrictions that interfere with stealth scripts.
    """
    return [
        "--disable-blink-features=AutomationControlled",
        "--no-first-run",
        "--no-default-browser-check",
    ]


async def inject_stealth_scripts(session: BrowserSession) -> None:
    """Inject all stealth JavaScript payloads via CDP.

    Uses browser-use's internal _cdp_add_init_script API, which adds the script
    to every new document load (equivalent to Playwright's
    addInitScript behavior).

    Args:
        session: A started BrowserSession instance

    Raises:
        RuntimeError: If session has no CDP connection
    """
    scripts = get_stealth_scripts()
    await session._cdp_add_init_script(scripts)
    logger.debug("Stealth scripts injected via CDP addScriptToEvaluateOnNewDocument")
