# -*- coding: utf-8 -*-
# Copyright (c) Alibaba, Inc. and its affiliates.

from dashscope.api_entities.dashscope_response import DashScopeAPIResponse
from dashscope.client.base_api import GetMixin, ListMixin, _get
from dashscope.common.utils import join_url
import dashscope


class Models(ListMixin, GetMixin):
    SUB_PATH = "models"

    @classmethod
    def get(  # type: ignore[override]
        cls,
        name: str,
        api_key: str = None,
        **kwargs,
    ) -> DashScopeAPIResponse:
        """Get the model information.

        Args:
            name (str): The model name.
            api_key (str, optional): The api key. Defaults to None.
            workspace (str): The dashscope workspace id.

        Returns:
            DashScopeAPIResponse: The model information.
        """
        from http import HTTPStatus

        # Use path parameter to get specific model
        # API endpoint: /api/v1/models/{name}
        url = join_url(dashscope.base_http_api_url, cls.SUB_PATH.lower(), name)

        response = _get(
            url,
            api_key=api_key,
            **kwargs,
        )

        return response  # type: ignore[return-value]

    @classmethod
    def list(  # type: ignore[override]
        cls,
        page=1,
        page_size=10,
        api_key: str = None,
        **kwargs,
    ) -> DashScopeAPIResponse:
        """List models.

        Args:
            api_key (str, optional): The api key
            page (int, optional): Page number. Defaults to 1.
            page_size (int, optional): Items per page. Defaults to 10.

        Returns:
            DashScopeAPIResponse: The models.
        """
        # type: ignore
        return super().list(page, page_size, api_key=api_key, **kwargs)  # type: ignore[return-value] # pylint: disable=line-too-long # noqa: E501
