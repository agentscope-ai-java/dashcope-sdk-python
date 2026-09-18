# -*- coding: utf-8 -*-
# Copyright (c) Alibaba, Inc. and its affiliates.

import os
from typing import Optional

import dashscope
from dashscope.common.constants import (
    DEFAULT_DASHSCOPE_API_KEY_FILE_PATH,
    DEFAULT_DASHSCOPE_CACHE_PATH,
)
from dashscope.common.error import AuthenticationError


def get_default_api_key():
    if dashscope.api_key is not None:
        # user set environment variable DASHSCOPE_API_KEY
        return dashscope.api_key
    elif dashscope.api_key_file_path:
        # user set environment variable DASHSCOPE_API_KEY_FILE_PATH
        with open(
            dashscope.api_key_file_path,
            "rt",
            encoding="utf-8",
        ) as f:  # open with text mode.
            return f.read().strip()
    else:  # Find the api key from default key file.
        if os.path.exists(DEFAULT_DASHSCOPE_API_KEY_FILE_PATH):
            with open(
                DEFAULT_DASHSCOPE_API_KEY_FILE_PATH,
                "rt",
                encoding="utf-8",
            ) as f:
                return f.read().strip()

    raise AuthenticationError(
        "No api key provided. You can set by dashscope.api_key = your_api_key in code, "  # noqa: E501  # pylint: disable=line-too-long
        "or you can set it via environment variable DASHSCOPE_API_KEY= your_api_key. "  # noqa: E501
        "You can store your api key to a file, and use dashscope.api_key_file_path=api_key_file_path in code, "  # noqa: E501  # pylint: disable=line-too-long
        "or you can set api key file path via environment variable DASHSCOPE_API_KEY_FILE_PATH, "  # noqa: E501  # pylint: disable=line-too-long
        "You can call save_api_key to api_key_file_path or default path(~/.dashscope/api_key).",  # noqa: E501  # pylint: disable=line-too-long
    )


def save_api_key(api_key: str, api_key_file_path: Optional[str] = None):
    """Persist an API key to a file so it does not need to be set on every run.

    Args:
        api_key (str): The DashScope API key to save.
        api_key_file_path (str, optional): Destination file path. Defaults to
            ``~/.dashscope/api_key``, which is also where the SDK looks for a
            key when neither ``dashscope.api_key`` nor
            ``dashscope.api_key_file_path`` is set.

    Examples:
        >>> from dashscope import save_api_key
        >>> save_api_key(api_key="YOUR-DASHSCOPE-API-KEY")

        Save to a custom location and point the SDK at it:

        >>> save_api_key(
        ...     api_key="YOUR-DASHSCOPE-API-KEY",
        ...     api_key_file_path="~/.dashscope/prod_api_key",
        ... )
        >>> import dashscope
        >>> dashscope.api_key_file_path = "~/.dashscope/prod_api_key"
    """
    if api_key_file_path is None:
        os.makedirs(DEFAULT_DASHSCOPE_CACHE_PATH, exist_ok=True)
        # pylint: disable=unspecified-encoding
        with open(DEFAULT_DASHSCOPE_API_KEY_FILE_PATH, "w+") as f:
            f.write(api_key)
    else:
        os.makedirs(os.path.dirname(api_key_file_path), exist_ok=True)
        # pylint: disable=unspecified-encoding
        with open(api_key_file_path, "w+") as f:
            f.write(api_key)
