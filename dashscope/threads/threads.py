# -*- coding: utf-8 -*-
# Copyright (c) Alibaba, Inc. and its affiliates.

import warnings
from typing import Dict, List, Optional

from dashscope.assistants.assistant_types import DeleteResponse
from dashscope.client.base_api import (
    CreateMixin,
    DeleteMixin,
    GetStatusMixin,
    UpdateMixin,
)
from dashscope.common.error import InputRequired
from dashscope.threads.thread_types import Run, Thread

__all__ = ["Threads"]

# Deprecation warning message
_DEPRECATION_MSG = (
    "The Assistants API (dashscope.threads) is deprecated and will be "
    "removed in a future release. Please migrate to the Responses API. "
    "See https://help.aliyun.com/zh/model-studio/synchronous-call-api-reference "
    "for migration details."
)


class Threads(CreateMixin, DeleteMixin, GetStatusMixin, UpdateMixin):
    """
    .. deprecated::
        The Threads API is deprecated and will be removed in a future release.
        Please migrate to the Responses API.
        See https://help.aliyun.com/zh/model-studio/synchronous-call-api-reference
        for migration details.
    """

    SUB_PATH = "threads"

    @classmethod
    def call(  # type: ignore[override]
        cls,
        *,
        messages: List[Dict] = None,
        metadata: Dict = None,
        workspace: str = None,
        api_key: str = None,
        **kwargs,
    ) -> Thread:
        """Create a thread.

        Args:
            messages (List[Dict], optional):
                List of messages to start thread. Defaults to None.
            metadata (Dict, optional):
                The key-value information associate with thread. Defaults to
                None.
            workspace (str, optional):
                The DashScope workspace id. Defaults to None.
            api_key (str, optional): Your DashScope api key. Defaults to None.

        Returns:
            Thread: The thread object.
        """
        return cls.create(
            messages=messages,
            metadata=metadata,
            workspace=workspace,
            api_key=api_key,
            **kwargs,
        )

    @classmethod
    def create(
        cls,
        *,
        messages: List[Dict] = None,
        metadata: Dict = None,
        workspace: str = None,
        api_key: str = None,
        **kwargs,
    ) -> Thread:
        """Create a thread.

        Args:
            messages (List[Dict], optional):
                List of messages to start thread. Defaults to None.
            metadata (Dict, optional):
                The key-value information associate with thread. Defaults to
                None.
            workspace (str, optional):
                The DashScope workspace id. Defaults to None.
            api_key (str, optional): Your DashScope api key. Defaults to None.

        Returns:
            Thread: The thread object.
        """
        warnings.warn(
            _DEPRECATION_MSG,
            category=DeprecationWarning,
            stacklevel=2,
        )
        data = {}
        if messages:
            data["messages"] = messages
        if metadata:
            data["metadata"] = metadata
        response = super().call(
            data=data if data else "",
            api_key=api_key,
            flattened_output=True,
            workspace=workspace,
            **kwargs,
        )
        return Thread(**response)

    @classmethod
    def get(  # type: ignore[override]
        cls,
        thread_id: str,
        *,
        workspace: str = None,
        api_key: str = None,
        **kwargs,
    ) -> Thread:
        """Retrieve the thread.

        Args:
            thread_id (str): The target thread.
            workspace (str, optional):
                The DashScope workspace id. Defaults to None.
            api_key (str, optional): Your DashScope api key. Defaults to None.

        Returns:
            Thread: The `Thread` information.
        """
        return cls.retrieve(
            thread_id,
            workspace=workspace,
            api_key=api_key,
            **kwargs,
        )

    @classmethod
    def retrieve(
        cls,
        thread_id: str,
        *,
        workspace: str = None,
        api_key: str = None,
        **kwargs,
    ) -> Thread:
        """Retrieve the thread.

        Args:
            thread_id (str): The target thread.
            workspace (str, optional):
                The DashScope workspace id. Defaults to None.
            api_key (str, optional): Your DashScope api key. Defaults to None.

        Returns:
            Thread: The `Thread` information.
        """
        warnings.warn(
            _DEPRECATION_MSG,
            category=DeprecationWarning,
            stacklevel=2,
        )
        if not thread_id:
            raise InputRequired("thread_id is required!")
        response = super().call(
            data={"thread_id": thread_id},
            api_key=api_key,
            flattened_output=True,
            workspace=workspace,
            **kwargs,
        )
        return Thread(**response)

    @classmethod
    def update(
        cls,
        thread_id: str,
        *,
        metadata: Dict = None,
        workspace: str = None,
        api_key: str = None,
        **kwargs,
    ) -> Thread:
        """Update the thread.

        Args:
            thread_id (str): The target thread.
            metadata (Dict, optional):
                The key-value information associate with thread. Defaults to
                None.
            workspace (str, optional):
                The DashScope workspace id. Defaults to None.
            api_key (str, optional): Your DashScope api key. Defaults to None.

        Returns:
            Thread: The `Thread` information.
        """
        warnings.warn(
            _DEPRECATION_MSG,
            category=DeprecationWarning,
            stacklevel=2,
        )
        if not thread_id:
            raise InputRequired("thread_id is required!")
        data = {"thread_id": thread_id}
        if metadata:
            data["metadata"] = metadata
        response = super().call(
            data=data,
            api_key=api_key,
            flattened_output=True,
            workspace=workspace,
            **kwargs,
        )
        return Thread(**response)

    @classmethod
    def delete(  # type: ignore[override]
        cls,
        thread_id: str,
        *,
        workspace: str = None,
        api_key: str = None,
        **kwargs,
    ) -> DeleteResponse:
        """Delete the thread.

        Args:
            thread_id (str): The target thread.
            workspace (str, optional):
                The DashScope workspace id. Defaults to None.
            api_key (str, optional): Your DashScope api key. Defaults to None.

        Returns:
            DeleteResponse: The delete response.
        """
        warnings.warn(
            _DEPRECATION_MSG,
            category=DeprecationWarning,
            stacklevel=2,
        )
        if not thread_id:
            raise InputRequired("thread_id is required!")
        response = super().call(
            data={"thread_id": thread_id},
            api_key=api_key,
            flattened_output=True,
            workspace=workspace,
            **kwargs,
        )
        return DeleteResponse(**response)
