# -*- coding: utf-8 -*-
# Copyright (c) Alibaba, Inc. and its affiliates.

from typing import Generator, List, Union

from dashscope.api_entities.dashscope_response import (
    DashScopeAPIResponse,
    DictMixin,
    Role,
)
from dashscope.client.base_api import BaseApi
from dashscope.common.constants import MESSAGE, SCENE
from dashscope.common.error import InputRequired, ModelRequired
from dashscope.common.utils import _get_task_group_and_task


class MessageParam(DictMixin):
    role: str

    def __init__(self, role: str, **kwargs):
        super().__init__(role=role, **kwargs)


class UserRoleMessageParam(MessageParam):
    content: str

    def __init__(self, content: str, **kwargs):
        super().__init__(role=Role.USER, content=content, **kwargs)


class AttachmentRoleMessageParam(MessageParam):
    meta: dict

    def __init__(self, meta: dict, **kwargs):
        super().__init__(role=Role.ATTACHMENT, meta=meta, **kwargs)


class OtherRoleContentMessageParam(MessageParam):
    content: str

    def __init__(self, role: str, content: str, **kwargs):
        super().__init__(role=role, content=content, **kwargs)


class OtherRoleMetaMessageParam(MessageParam):
    meta: dict

    def __init__(self, role: str, meta: dict, **kwargs):
        super().__init__(role=role, meta=meta, **kwargs)


class CodeGeneration(BaseApi):
    function = "generation"
    """API for AI-Generated Content(AIGC) models.

    """

    class Models:
        tongyi_lingma_v1 = "tongyi-lingma-v1"

    class Scenes:
        custom = "custom"
        nl2code = "nl2code"
        code2comment = "code2comment"
        code2explain = "code2explain"
        commit2msg = "commit2msg"
        unit_test = "unittest"
        code_qa = "codeqa"
        nl2sql = "nl2sql"

    @classmethod
    def call(  # type: ignore[override]
        cls,
        model: str,
        scene: str = None,
        api_key: str = None,
        message: List[MessageParam] = None,
        workspace: str = None,
        **kwargs,
    ) -> Union[
        DashScopeAPIResponse,
        Generator[
            DashScopeAPIResponse,
            None,
            None,
        ],
    ]:
        """Call generation model service.

        Args:
            model (str): The requested model, such as tongyi-lingma-v1
            scene (str): Task type, one of ``CodeGeneration.Scenes``:
                ``custom`` (freeform prompt), ``nl2code`` (natural language
                to code), ``code2comment`` (add comments), ``code2explain``
                (explain code), ``commit2msg`` (generate a commit message
                from a diff), ``unittest`` (generate unit tests), ``codeqa``
                (code Q&A), ``nl2sql`` (natural language to SQL). Each scene
                expects a different ``message`` shape; see Examples below.
            api_key (str, optional): The api api_key, can be None,
                if None, will get by default rule(TODO: api key doc).
            message (list): The generation messages. Typically a ``user``
                message carrying the instruction, optionally followed by an
                ``attachment`` message whose ``meta`` supplies the code,
                diff, or schema the scene operates on (see Examples below
                for the exact shape per scene).
            workspace (str): The dashscope workspace id.
            **kwargs:
                n (int, `optional`): The number of output results,
                    currently only supports 1, with a default value of 1.

        Returns:
            Union[DashScopeAPIResponse,
                  Generator[DashScopeAPIResponse, None, None]]: If
            stream is True, return Generator, otherwise DashScopeAPIResponse.

        Examples:
            Natural language to code (``nl2code``):

            >>> from dashscope import CodeGeneration
            >>> response = CodeGeneration.call(
            ...     model=CodeGeneration.Models.tongyi_lingma_v1,
            ...     scene=CodeGeneration.Scenes.nl2code,
            ...     message=[
            ...         {"role": "user", "content": "Compute the total size of all files under a given path"},
            ...         {"role": "attachment", "meta": {"language": "python"}},
            ...     ],
            ... )
            >>> print(response.output)

            Explain existing code (``code2explain``):

            >>> response = CodeGeneration.call(
            ...     model=CodeGeneration.Models.tongyi_lingma_v1,
            ...     scene=CodeGeneration.Scenes.code2explain,
            ...     message=[
            ...         {"role": "user", "content": "Explain in at least 200 words"},
            ...         {"role": "attachment", "meta": {"code": "public int getHeaderCacheSize() { return 0; }", "language": "java"}},
            ...     ],
            ... )
            >>> print(response.output)
        """
        if (scene is None or not scene) or (message is None or not message):
            raise InputRequired("scene and message is required!")
        if model is None or not model:
            raise ModelRequired("Model is required!")
        task_group, task = _get_task_group_and_task(__name__)
        (
            input,  # pylint: disable=redefined-builtin
            parameters,
        ) = cls._build_input_parameters(
            model,
            scene,
            message,
            **kwargs,
        )
        response = super().call(
            model=model,
            task_group=task_group,
            task=task,
            function=CodeGeneration.function,
            api_key=api_key,
            input=input,
            workspace=workspace,
            is_service=False,
            **parameters,
        )

        is_stream = kwargs.get("stream", False)
        if is_stream:
            return (rsp for rsp in response)
        else:
            return response

    @classmethod
    def _build_input_parameters(
        cls,
        model,
        scene,
        message,
        **kwargs,
    ):  # pylint: disable=unused-argument
        parameters = {"n": kwargs.pop("n", 1)}
        input = {  # pylint: disable=redefined-builtin
            SCENE: scene,
            MESSAGE: message,
        }
        return input, {**parameters, **kwargs}
