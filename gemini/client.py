# Copyright 2024 Daniel Park, Antonio Cheang, MIT License
import os
import re
import json
import time
import httpx
import random
import string
import urllib
import asyncio
import requests
from typing import Optional, Any, List

from .constants import (
    HEADERS,
    SUPPORTED_BROWSERS,
    BOT_SERVER,
    SHARE_ENDPOINT,
    POST_ENDPOINT,
    HOST,
)


class GeminiClient:
    """
    A client for interacting with various services, featuring automatic cookie management, proxy configuration, Google Cloud Translation integration, and optional code execution in IPython environments.

    Attributes:
        session (httpx.AsyncClient): An asynchronous HTTP client for making requests.
        cookies (Dict[str, str]): A dictionary of cookies for session management.
        timeout (int): Timeout for requests in seconds, defaulting to 30.
        proxies (Dict[str, str]): Configuration for request proxies.
        language (Optional[str]): Language code for translation services (e.g., "en", "ko", "ja").
        auto_cookies (bool): Flag for automatic cookie retrieval and management, defaulting to False.
        google_translator_api_key (Optional[str]): API key for Google Cloud Translation services.
        run_code (bool): Flag for executing code in IPython environments.
        verify (bool): Flag for SSL certificate verification in HTTP requests.
        latency (int): Latency consideration in operations, defaulting to 10.
        update_cookie_list (List[str]): List of cookies to be updated, if any.
    """

    __slots__ = [
        "session",
        "token",
        "cookies",
        "timeout",
        "proxies",
        "language",
        "auto_cookies",
        "run_code",
        "verify",
        "_reqid",
        "latency",
        "running",
        "auto_close",
        "close_delay",
    ]

    def __init__(
        self,
        auto_cookies: bool = False,
        token: str = None,
        session: Optional[httpx.AsyncClient] = None,
        cookies: Optional[dict] = {},
        timeout: int = 30,
        proxies: Optional[dict] = {},
        language: Optional[str] = None,
        verify: bool = True,
        latency: int = 10,
        auto_close=True,
        close_delay: int = 60,
    ):
        """
        Initializes a new GeminiClient instance with various configurations for HTTP requests and service interactions.

        Args:
            auto_cookies (bool): If True, enables automatic management of cookies.
            token (str, optional): Authentication token used for session management. Defaults to None.
            session (httpx.AsyncClient, optional): An instance of httpx.AsyncClient for making asynchronous HTTP requests. If None, a new session will be created. Defaults to None.
            cookies (dict, optional): Initial cookies to be used with the session. Defaults to an empty dictionary.
            timeout (int): The timeout for requests in seconds. Defaults to 30.
            proxies (dict, optional): A dictionary of proxy configurations to be used with the session. Defaults to an empty dictionary.
            language (str, optional): The default language code to be used for translation services. Defaults to None.
            google_translator_api_key (str, optional): The API key for Google Cloud Translation services. Defaults to None.
            run_code (bool): If True, enables the execution of code in IPython environments. Defaults to False.
            verify (bool): If True, enables SSL certificate verification for HTTP requests. Defaults to True.
            latency (int): The latency in seconds to consider for operations, affecting retry and backoff strategies. Defaults to 10.
            update_cookie_list (List[str], optional): A list of cookies that should be updated during session management. Defaults to an empty list.
            auto_close (bool): If True, the session will automatically close after a specified delay. Defaults to True.
            close_delay (int): The delay in seconds before the session is automatically closed, applicable if auto_close is True. Defaults to 60.
        """
        self.auto_cookies = auto_cookies
        self.latency = latency
        self.running = False
        self._reqid = int("".join(random.choices(string.digits, k=4)))
        self.cookies = cookies
        self._get_cookies(auto_cookies)
        self.proxies = proxies or {}
        self.timeout = timeout
        self.session = session
        self.token = token
        self.token = self.get_nonce_value()
        self.language = language or os.getenv("GEMINI_LANGUAGE")
        self.verify = verify
        self.auto_close = auto_close
        self.close_delay = close_delay

    async def async_init(
        self,
    ) -> None:
        """
        Initializes the asynchronous session with optional auto-close functionality.

        Args:
            auto_close (bool): Flag to enable automatic session closure.
            close_delay (int): Delay in seconds before automatically closing the session.
        """
        self.session = await self._create_async_session(
            auto_close=self.auto_close, close_delay=self.close_delay
        )

    async def _create_async_session(
        self, auto_close: bool, close_delay: int
    ) -> httpx.AsyncClient:
        """
        Initializes or configures the httpx.AsyncClient session with predefined session headers, proxies, and cookies.

        Returns:
            httpx.AsyncClient: The session object, configured with headers, proxies, and cookies.

        Raises:
            ValueError: If the 'cookies' dictionary is empty, indicating that there's insufficient information to properly set up a new session.
        """
        if self.session is not None:
            return self.session

        print(self.cookies)
        if not self.cookies:
            raise ValueError("Failed to set session. 'cookies' dictionary is empty.")

        self.session = httpx.AsyncClient(
            headers=HEADERS,
            cookies=self.cookies,
            proxies=self.proxies,
            timeout=self.timeout,
        )

        if hasattr(self, "session"):
            self.running = True
        else:
            self.running = False

        return self.session

    async def close(self):
        if self.session:
            await self.session.aclose()
            self.session = None

    async def reset_close_task(self) -> None:
        """
        Resets the close task, cancelling any existing task and creating a new one.
        """
        if self.close_task:
            self.close_task.cancel()
            self.close_task = None
        self.close_task = asyncio.create_task(self.close_session())

    def check_session_cookies(self) -> None:
        """
        Prints the current session's cookies. Indicates if the session is uninitialized.
        """
        if self.session:
            cookies_str = "\n".join(
                f"{key}: {value}" for key, value in self.session.cookies.items()
            )
            print("Session Cookies:\n" + cookies_str)
        else:
            print("Session not initialized.")

    def check_session_headers(self) -> None:
        """
        Prints the current session's headers. Indicates if the session is uninitialized.
        """
        if self.session:
            headers = self.session.headers
            headers_str = "\n".join(f"{key}: {value}" for key, value in headers.items())
            print("Session Headers:\n" + headers_str)
        else:
            print("Session not initialized.")

    def get_nonce_value(self) -> str:
        """
        Get the Nonce Token value from the Gemini API response.
        """
        error_message = "Nonce token value not found or response status is not 200."

        with requests.Session() as session:
            response = session.get(HOST, timeout=self.timeout, proxies=self.proxies)
            if response.status_code == 200:
                match = re.search(r'nonce="([^"]+)"', response.text)
                if match:
                    return match.group(1)
            raise Exception(error_message)

    def _get_cookies(self, auto_cookies: bool) -> None:
        """
        Updates the instance's cookies attribute with Gemini API tokens, either from environment variables or by extracting them from the browser, based on the auto_cookies flag. If self.cookies already contains cookies, it will use these existing cookies and not attempt to update them.
        """
        # Initialize cookies dictionary if not already initialized
        if not hasattr(self, "cookies"):
            self.cookies = {}

        # If cookies already exist, skip updating and use the existing ones
        if self.cookies:  # Check if self.cookies is not empty
            print("Using existing cookies.")
            return  # Exit the method if cookies already exist

        # Attempt to load cookies automatically from the browser if necessary
        if auto_cookies and not self.cookies:
            try:
                self._get_cookies_from_browser()
            except Exception as e:
                raise Exception("Failed to extract cookies from browser.") from e

        # Warning if no cookies are available and auto_cookies is False
        if not auto_cookies and not self.cookies:
            print(
                "Cookie loading issue, try setting auto_cookies to True. Restart browser, log out, log in for Gemini Web UI to work. Keep a single browser open."
            )
            try:
                self.auto_cookies = True
                self._get_cookies_from_browser()
            except Exception as e:
                print(e)

        # Raise an exception if still no cookies
        if not self.cookies:
            raise Exception(
                "Gemini cookies must be provided through environment variables or extracted from the browser with auto_cookies enabled."
            )

    def _get_cookies_from_browser(self) -> dict:
        """
        Attempts to extract specific Gemini cookies from the cookies stored by web browsers on the current system.

        This method iterates over a predefined list of supported browsers, attempting to retrieve cookies that match a specific domain (e.g., ".google.com"). If the required cookies are found, they are added to the instance's cookie store. The process supports multiple modern web browsers across different operating systems.

        The method updates the instance's `cookies` attribute with any found cookies that match the specified criteria.

        Raises:
            ValueError: If no supported browser is found with the required cookies, or if an essential cookie is missing after attempting retrieval from all supported browsers.
        """

        for browser_fn in SUPPORTED_BROWSERS:
            try:
                print(
                    f"Trying to automatically retrieve cookies from {browser_fn} using the browser_cookie3 package."
                )
                cj = browser_fn(domain_name=".google.com")
                found_cookies = {cookie.name: cookie.value for cookie in cj}
                if len(found_cookies) >= 5:
                    print(
                        f"Successfully retrieved cookies from {browser_fn}.\n{found_cookies}"
                    )
                    self.cookies = found_cookies
                    break
                else:
                    print(
                        f"Automatically configure cookies with detected ones but found only {len(found_cookies)} cookies.\n{found_cookies}"
                    )
            except Exception as e:
                print(e)
                continue

        if not self.cookies:
            raise ValueError(
                "Failed to get cookies. Set 'cookies' argument or 'auto_cookies' as True."
            )

    def _update_cookies(self, update_cookie_list: List[str] = None):
        """
        Updates specified cookies in the httpx client. If update_cookie_list is not provided,
        updates all cookies stored in self.cookies.

        Parameters:
        - update_cookie_list (List[str], optional): A list of cookie names to update.
                                                If None, updates all cookies from self.cookies.
        """
        self._get_cookies(True)

        cookies_to_update = (
            {k: self.cookies[k] for k in update_cookie_list}
            if update_cookie_list is not None
            else self.cookies
        )

        try:
            for cookie_name, cookie_value in cookies_to_update.items():
                if cookie_value:
                    self.session.cookies.set(cookie_name, cookie_value)
                    print(f"Succefully update cookies: {cookies_to_update}")
                else:
                    print(
                        f"Warning: Cookie value for {cookie_name} is missing; skipping update."
                    )
        except Exception as e:
            print(f"An error occurred while updating cookies: {e}")

    def _construct_params(self, sid: str) -> str:
        """
        Constructs URL-encoded parameters for a request.

        Parameters:
            sid (str): The session ID.

        Returns:
            str: URL-encoded string of parameters.
        """
        return urllib.parse.urlencode(
            {
                "bl": BOT_SERVER,
                "hl": os.environ.get("GEMINI_LANGUAGE", "en"),
                "_reqid": self.get_reqid(),
                "rt": "c",
                "f.sid": sid,
            }
        )

    def _construct_payload(self, prompt: str, nonce: str) -> str:
        """
        Constructs URL-encoded payload for a request.

        Parameters:
            prompt (str): The user prompt to send.
            nonce (str): A one-time token used for request verification.

        Returns:
            str: URL-encoded string of the payload.
        """
        return urllib.parse.urlencode(
            {
                "at": nonce,
                "f.req": json.dumps([None, json.dumps([[prompt], None, None])]),
            }
        )

    async def post_prompt(
        self,
        prompt: str,
    ) -> dict:
        data = self._construct_payload(prompt)
        params = self._construct_params()

        response = await self.session.post(
            POST_ENDPOINT,
            data=data,
            params=params,
            timeout=self.timeout,
        )
        self._reqid += 100000

        return response

    async def generate_content(self, prompt: str) -> dict:
        try:
            response = await self.post_prompt(prompt)
            response_data = await response.json()
            response_status_code = response.status

            if response_status_code != 200:
                raise ValueError(f"Response status: {response_status_code}")
            return response_data
        except Exception as e:
            print(f"An error occurred: {e}")
            return {}

    async def request_share(
        self,
    ) -> dict:
        """
        Asynchronously generates content by querying the Gemini API, supporting text and optional image input alongside a specified tool for content generation.

        Args:
            session (Optional[GeminiSession]): A session object for the Gemini API, if None, a new session is created or a default session is used.

        Returns:
            dict: A dictionary containing the response from the Gemini API.
        """

        async with httpx.AsyncClient() as session:
            try:
                async with session.post(
                    SHARE_ENDPOINT, timeout=self.timeout
                ) as response:
                    return await response.json()
            except asyncio.TimeoutError:
                raise TimeoutError(
                    "Request timed out. If errors persist, increase the timeout parameter in the Gemini class to a higher number of seconds."
                )
