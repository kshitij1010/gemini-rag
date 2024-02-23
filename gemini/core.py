# Copyright 2024 Minwoo(Daniel) Park, MIT License
import base64
import json
import os
import random
import re
import string
import uuid
import requests
from typing import Optional

try:
    from langdetect import detect
    from deep_translator import GoogleTranslator
    from google.cloud import translate_v2 as translate
except ImportError:
    pass
from .constants import (
    ALLOWED_LANGUAGES,
    REPLIT_SUPPORT_PROGRAM_LANGUAGES,
    SESSION_HEADERS,
    TEXT_GENERATION_WEB_SERVER_PARAM,
    Tool,
)
from .utils import (
    build_export_data_structure,
    build_input_replit_data_struct,
    extract_cookies_from_brwoser,
    upload_image,
)
from .models.base import (
    GeminiOutput,
    Candidate,
    WebImage,
    GeneratedImage,
)
from .models.exceptions import (
    APIError,
    GeminiError,
    TimeoutError,
)
from .models.session import GeminiSession


class Gemini:
    """
    Represents a Gemini instance for interacting with the Google Gemini service.

    Attributes:
        session (requests.Session): Requests session object.
        cookies (dict): Dictionary containing cookies (__Secure-1PSID, __Secure-1PSIDTS, __Secure-1PSIDCC) with their respective values.
        timeout (int): Request timeout in seconds. Defaults to 20.
        proxies (dict): Proxy configuration for requests.
        language (str): Natural language code for translation (e.g., "en", "ko", "ja").
        conversation_id (str): ID for fetching conversational context.
        auto_cookies (bool): Flag indicating whether to retrieve a token from the browser.
        google_translator_api_key (str): Google Cloud Translation API key.
        run_code (bool): Flag indicating whether to execute code included in the answer (IPython only).
    """

    __slots__ = [
        "session",
        "cookies",
        "timeout",
        "proxies",
        "language",
        "conversation_id",
        "auto_cookies",
        "google_translator_api_key",
        "run_code",
    ]

    def __init__(
        self,
        session: Optional[requests.Session] = None,
        cookies: dict = None,
        timeout: int = 20,
        proxies: Optional[dict] = None,
        language: Optional[str] = None,
        conversation_id: Optional[str] = None,
        google_translator_api_key: Optional[str] = None,
        run_code: bool = False,
        auto_cookies: bool = False,
    ):
        """
        Initialize the Gemini instance.

        Args:
            session (requests.Session, optional): Requests session object.
            cookies (dict, optional): Dictionary containing cookies (__Secure-1PSID, __Secure-1PSIDTS, __Secure-1PSIDCC) with their respective values.
            timeout (int, optional): Request timeout in seconds. Defaults to 20.
            proxies (dict, optional): Proxy configuration for requests.
            language (str, optional): Natural language code for translation (e.g., "en", "ko", "ja").
            conversation_id (str, optional): ID for fetching conversational context.
            google_translator_api_key (str, optional): Google Cloud Translation API key.
            run_code (bool, optional): Flag indicating whether to execute code included in the answer (IPython only).
            auto_cookies (bool, optional): Flag indicating whether to retrieve a token from the browser.
        """
        self.session = self._get_session(session)
        self.cookies = cookies or self._get_auto_cookies(auto_cookies)
        self.timeout = timeout
        self.proxies = proxies
        self.language = language or os.getenv("GEMINI_LANGUAGE")
        self.conversation_id = conversation_id or ""
        self.google_translator_api_key = google_translator_api_key
        self.run_code = run_code
        self._reqid = int("".join(random.choices(string.digits, k=4)))
        self.response_id = ""
        self.choice_id = ""
        self.og_pid = ""
        self.rot = ""
        self.exp_id = ""
        self.init_value = ""

    def _get_auto_cookies(self, auto_cookies: bool) -> dict:
        """
        Get the Gemini API token either from the provided token or from the browser cookie.

        Args:
            auto_cookies (bool): Whether to extract the token from the browser cookie.

        Returns:
            dict: The dictionary containing the extracted cookies.

        Raises:
            Exception: If the token is not provided and can't be extracted from the browser.
        """
        env_cookies = os.getenv("GEMINI_COOKIES_DICT")
        if env_cookies:
            return env_cookies

        if auto_cookies:
            extracted_cookie_dict = extract_cookies_from_brwoser()
            self.cookies = extracted_cookie_dict
            if extracted_cookie_dict:
                return extracted_cookie_dict

        raise Exception(
            "Gemini cookies must be provided as the 'cookies' argument or extracted from the browser."
        )

    def _get_session(self, session: Optional[requests.Session]) -> requests.Session:
        """
        Get the requests Session object.

        Args:
            session (requests.Session): Requests session object.

        Returns:
            requests.Session: The Session object.
        """
        if session is not None:
            return session
        elif not self.cookies:
            raise ValueError("'cookies' dictionary is empty.")

        session = requests.Session()
        session.headers = SESSION_HEADERS
        session.cookies.set("__Secure-1PSID", self.cookies["__Secure-1PSID"])
        session.proxies = self.proxies

        if self.cookies is not None:
            session.cookies.update(self.cookies)

        return session

    def _get_snim0e(self) -> str:
        """
        Get the SNlM0e value from the Gemini API response.

        Returns:
            str: SNlM0e value.
        Raises:
            Exception: If the __Secure-1PSID value is invalid or SNlM0e value is not found in the response.
        """
        response = self.session.get(
            "https://gemini.google.com/app", timeout=self.timeout, proxies=self.proxies
        )
        if response.status_code != 200:
            raise Exception(
                f"Response status code is not 200. Response Status is {response.status_code}"
            )
        snim0e = re.search(r"SNlM0e\":\"(.*?)\"", response.text)
        if not snim0e:
            raise Exception(
                "SNlM0e value not found. Double-check cookies dict value or pass it as Gemini(cookies=Dict())"
            )
        return snim0e.group(1)

    def generate_content(
        self,
        prompt: str,
        session: Optional["GeminiSession"] = None,
        image: Optional[bytes] = None,
        tool: Optional[Tool] = None,
    ) -> dict:
        """
        Get an answer from the Gemini API for the given input text.

        Example:
        >>> cookies = Dict()
        >>> Gemini = Gemini(cookies=cookies)
        >>> response = Gemini.get_answer("나와 내 동년배들이 좋아하는 뉴진스에 대해서 알려줘")
        >>> print(response['content'])

        Args:
            prompt (str): Input text for the query.
            image (bytes): Input image bytes for the query, support image types: jpeg, png, webp
            image_name (str): Short file name
            tool : tool to use can be one of Gmail, Google Docs, Google Drive, Google Flights, Google Hotels, Google Maps, Youtube

        Returns:
            dict: Answer from the Gemini API in the following format:
                {
                    "content": str,
                    "conversation_id": str,
                    "response_id": str,
                    "factuality_queries": list,
                    "text_query": str,
                    "choices": list,
                    "links": list,
                    "images": list,
                    "program_lang": str,
                    "code": str,
                    "status_code": int
                }
        """
        if self.google_translator_api_key is not None:
            google_official_translator = translate.Client(
                api_key=self.google_translator_api_key
            )

        # [Optional] Language translation
        if (
            self.language is not None
            and self.language not in ALLOWED_LANGUAGES
            and self.google_translator_api_key is None
        ):
            translator_to_eng = GoogleTranslator(source="auto", target="en")
            prompt = translator_to_eng.translate(prompt)
        elif (
            self.language is not None
            and self.language not in ALLOWED_LANGUAGES
            and self.google_translator_api_key is not None
        ):
            prompt = google_official_translator.translate(prompt, target_language="en")
        data = {
            "at": self.SNlM0e,
            "f.req": json.dumps(
                [None, json.dumps([[prompt], None, session and session.metadata])]
            ),
        }

        # Get response
        try:
            response = self.session.post(
                "https://gemini.google.com/_/BardChatUi/data/assistant.lamda.BardFrontendService/StreamGenerate",
                data=data,
                timeout=self.timeout,
                proxies=self.proxies,
            )
        except:
            raise TimeoutError(
                "Request timed out. If errors persist, increase the timeout parameter in the Gemini class to a higher number of seconds."
            )

        if response.status_code != 200:
            raise APIError(f"Request failed with status code {response.status_code}")
        else:
            try:
                body = json.loads(
                    json.loads(response.text.split("\n")[2])[0][2]
                )  # Generated texts
                if not body[4]:
                    body = json.loads(
                        json.loads(response.text.split("\n")[2])[4][2]
                    )  # Non-textual data formats.
                if not body[4]:
                    raise APIError(
                        "Failed to parse body. The response body is unstructured. Please try again."
                    )  # Fail to parse
            except Exception:
                raise APIError(
                    "Failed to parse candidates. Unexpected structured response returned. Please try again."
                )  # Unexpected structured response

            try:
                candidates = []
                for candidate in body[4]:
                    web_images = (
                        candidate[4]
                        and [
                            WebImage(
                                url=image[0][0][0], title=image[2], alt=image[0][4]
                            )
                            for image in candidate[4]
                        ]
                        or []
                    )
                    generated_images = (
                        candidate[12]
                        and candidate[12][7]
                        and candidate[12][7][0]
                        and [
                            GeneratedImage(
                                url=image[0][3][3],
                                title=f"[Generated image {image[3][6]}]",
                                alt=image[3][5][i],
                                cookies=self.cookies,
                            )
                            for i, image in enumerate(candidate[12][7][0])
                        ]
                        or []
                    )
                    candidates.append(
                        Candidate(
                            rcid=candidate[0],
                            text=candidate[1][0],
                            web_images=web_images,
                            generated_images=generated_images,
                        )
                    )
                if not candidates:
                    raise GeminiError(
                        "Failed to generate candidates. No data of any kind returned."
                    )
                generated_content = GeminiOutput(
                    metadata=body[1], candidates=candidates
                )
            except IndexError:
                raise APIError(
                    "Failed to parse response body. Data structure is invalid."
                )

        if not generated_content:
            # Retry to generate content by updating cookies and session
            for _ in range(2):
                self.cookies = self._get_auto_cookies(True)
                self.session = self._get_session(None)
                try:
                    generated_content = self.generate_content(
                        prompt, session, image, tool
                    )
                    break
                except:
                    continue
            else:
                raise APIError("Failed to establish session connection after retrying.")

        return generated_content

    def speech(self, prompt: str, lang: str = "en-US") -> dict:
        """
        Get speech audio from Gemini API for the given input text.

        Example:
        >>> cookies = Dict()
        >>> Gemini = Gemini(cookies=cookies)
        >>> audio = Gemini.speech("Say hello!")
        >>> with open("Gemini.ogg", "wb") as f:
        >>>     f.write(bytes(audio['audio']))

        Args:
            prompt (str): Input text for the query.
            lang (str, optional, default = "en-US"): Input language for the query.

        Returns:
            dict: Answer from the Gemini API in the following format:
            {
                "audio": bytes,
                "status_code": int
            }
        """
        params = {
            "bl": TEXT_GENERATION_WEB_SERVER_PARAM,
            "_reqid": str(self._reqid),
            "rt": "c",
        }

        prompt_struct = [[["XqA3Ic", json.dumps([None, prompt, lang, None, 2])]]]

        data = {
            "f.req": json.dumps(prompt_struct),
            "at": self.SNlM0e,
        }

        # Get response
        response = self.session.post(
            "https://gemini.google.com/_/BardChatUi/data/batchexecute",
            params=params,
            data=data,
            timeout=self.timeout,
            proxies=self.proxies,
        )

        # Post-processing of response
        response_dict = json.loads(response.content.splitlines()[3])[0][2]
        if not response_dict:
            return {
                "content": f"Response Error: {response.content}. "
                f"\nUnable to get response."
                f"\nPlease double-check the cookie values and verify your network environment or google account."
            }
        resp_json = json.loads(response_dict)
        audio_b64 = resp_json[0]
        audio_bytes = base64.b64decode(audio_b64)
        return {"audio": audio_bytes, "status_code": response.status_code}

    def export_conversation(self, generated_content, title: str = "") -> dict:
        """
        Get Share URL for specific answer from Gemini

        Example:
        >>> cookies = Dict()
        >>> Gemini = Gemini(cookies = cookies)
        >>> generated_content = Gemini.get_answer("hello!")
        >>> url = Gemini.export_conversation(generated_content, title="Export Conversation")
        >>> print(url['url'])

        Args:
            generated_content (dict): generated_content returned from get_answer
            title (str, optional, default = ""): Title for URL
        Returns:
            dict: Answer from the Gemini API in the following format:
            {
                "url": str,
                "status_code": int
            }
        """
        conv_id = generated_content["conversation_id"]
        resp_id = generated_content["response_id"]
        choice_id = generated_content["choices"][0]["id"]
        params = {
            "rpcids": "fuVx7",
            "source-path": "/",
            "bl": TEXT_GENERATION_WEB_SERVER_PARAM,
            "rt": "c",
        }

        # Build data structure
        export_data_structure = build_export_data_structure(
            conv_id, resp_id, choice_id, title
        )

        data = {
            "f.req": json.dumps(export_data_structure),
            "at": self.SNlM0e,
        }
        response = self.session.post(
            "https://gemini.google.com/_/BardChatUi/data/batchexecute",
            params=params,
            data=data,
            timeout=self.timeout,
            proxies=self.proxies,
        )

        # Post-processing of response
        response_dict = json.loads(response.content.splitlines()[3])
        url_id = json.loads(response_dict[0][2])[2]
        url = f"https://g.co/Gemini/share/{url_id}"

        # Increment request ID
        self._reqid += 100000
        return {"url": url, "status_code": response.status_code}

    def export_replit(
        self,
        code: str,
        program_lang: Optional[str] = None,
        filename: Optional[str] = None,
        **kwargs,
    ) -> dict:
        """
        Get export URL to repl.it from code

        Example:
        >>> cookies = Dict()
        >>> Gemini = Gemini(cookies = cookies)
        >>> generated_content = Gemini.get_answer("Give me python code to print hello world")
        >>> url = Gemini.export_replit(generated_content['code'], generated_content['program_lang'])
        >>> print(url['url'])

        Args:
            code (str): source code
            program_lang (str, optional): programming language
            filename (str, optional): filename
            **kwargs: instructions, source_path
        Returns:
        dict: Answer from the Gemini API in the following format:
            {
                "url": str,
                "status_code": int
            }
        """
        params = {
            "rpcids": "qACoKe",
            "source-path": kwargs.get("source_path", "/"),
            "bl": TEXT_GENERATION_WEB_SERVER_PARAM,
            "_reqid": str(self._reqid),
            "rt": "c",
        }

        # Reference: https://github.com/jincheng9/markdown_supported_languages
        if program_lang not in REPLIT_SUPPORT_PROGRAM_LANGUAGES and filename is None:
            raise Exception(
                f"Language {program_lang} not supported, please set filename manually."
            )

        filename = (
            REPLIT_SUPPORT_PROGRAM_LANGUAGES.get(program_lang, filename)
            if filename is None
            else filename
        )
        input_replit_data_struct = build_input_replit_data_struct(
            kwargs.get("instructions", ""), code, filename
        )

        data = {
            "f.req": json.dumps(input_replit_data_struct),
            "at": self.SNlM0e,
        }

        # Get response
        response = self.session.post(
            "https://gemini.google.com/_/BardChatUi/data/batchexecute",
            params=params,
            data=data,
            timeout=self.timeout,
            proxies=self.proxies,
        )

        response_dict = json.loads(response.content.splitlines()[3])
        print(f"Response: {response_dict}")

        url = json.loads(response_dict[0][2])[0]

        # Increment request ID
        self._reqid += 100000

        return {"url": url, "status_code": response.status_code}

    def _extract_links(self, data: list) -> list:
        """
        Extract links from the given data.

        Args:
            data: Data to extract links from.

        Returns:
            list: Extracted links.
        """
        links = []
        if isinstance(data, list):
            for item in data:
                if isinstance(item, list):
                    links.extend(self._extract_links(item))
                elif (
                    isinstance(item, str)
                    and item.startswith("http")
                    and "favicon" not in item
                ):
                    links.append(item)
        return links


class GeminiSession:
    """
    Chat data to retrieve conversation history. Only if all 3 ids are provided will the conversation history be retrieved.

    Parameters
    ----------
    gemini: `Gemini`
        Gemini client interface for https://gemini.google.com/
    metadata: `list[str]`, optional
        List of chat metadata `[cid, rid, rcid]`, can be shorter than 3 elements, like `[cid, rid]` or `[cid]` only
    cid: `str`, optional
        Chat id, if provided together with metadata, will override the first value in it
    rid: `str`, optional
        Reply id, if provided together with metadata, will override the second value in it
    rcid: `str`, optional
        Reply candidate id, if provided together with metadata, will override the third value in it
    """

    # @properties needn't have their slots pre-defined
    __slots__ = ["__metadata", "gemini", "gemini_output"]

    def __init__(
        self,
        gemini: Gemini,
        metadata: Optional[list[str]] = None,
        cid: Optional[str] = None,  # chat id
        rid: Optional[str] = None,  # reply id
        rcid: Optional[str] = None,  # reply candidate id
    ):
        self.__metadata: list[Optional[str]] = [None, None, None]
        self.gemini: Gemini = gemini
        self.gemini_output: Optional[GeminiOutput] = None

        if metadata:
            self.metadata = metadata
        if cid:
            self.cid = cid
        if rid:
            self.rid = rid
        if rcid:
            self.rcid = rcid

    def __str__(self):
        return f"GeminiSession(cid='{self.cid}', rid='{self.rid}', rcid='{self.rcid}')"

    __repr__ = __str__

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)
        if name == "gemini_output" and isinstance(value, GeminiOutput):
            self.metadata = value.metadata
            self.rcid = value.rcid

    def send_message(self, prompt: str) -> GeminiOutput:
        """
        Generates contents with prompt.
        Use as a shortcut for `Gemini.generate_content(prompt, self)`.

        Parameters
        ----------
        prompt: `str`
            Prompt provided by user

        Returns
        -------
        :class:`GeminiOutput`
            Output data from gemini.google.com, use `GeminiOutput.text` to get the default text reply, `GeminiOutput.images` to get a list
            of images in the default reply, `GeminiOutput.candidates` to get a list of all answer candidates in the gemini_output
        """
        return self.gemini.generate_content(prompt, self)

    def choose_candidate(self, index: int) -> GeminiOutput:
        """
        Choose a candidate from the last `GeminiOutput` to control the ongoing conversation flow.

        Parameters
        ----------
        index: `int`
            Index of the candidate to choose, starting from 0
        """
        if not self.gemini_output:
            raise ValueError(
                "No previous gemini_output data found in this chat session."
            )

        if index >= len(self.gemini_output.candidates):
            raise ValueError(
                f"Index {index} exceeds the number of candidates in last model gemini_output."
            )

        self.gemini_output.chosen = index
        self.rcid = self.gemini_output.rcid
        return self.gemini_output

    @property
    def metadata(self):
        return self.__metadata

    @metadata.setter
    def metadata(self, value: list[str]):
        if len(value) > 3:
            raise ValueError("metadata cannot exceed 3 elements")
        self.__metadata[: len(value)] = value

    @property
    def cid(self):
        return self.__metadata[0]

    @cid.setter
    def cid(self, value: str):
        self.__metadata[0] = value

    @property
    def rid(self):
        return self.__metadata[1]

    @rid.setter
    def rid(self, value: str):
        self.__metadata[1] = value

    @property
    def rcid(self):
        return self.__metadata[2]

    @rcid.setter
    def rcid(self, value: str):
        self.__metadata[2] = value
