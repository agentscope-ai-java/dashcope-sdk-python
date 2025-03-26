# Copyright (c) Alibaba, Inc. and its affiliates.

from http import HTTPStatus

from dashscope import ImageSynthesis
from dashscope.common.constants import TaskStatus
from tests.base_test import BaseTestEnvironment


class TestAsyncImageSynthesisRequest(BaseTestEnvironment):
    @classmethod
    def setup_class(cls):
        super().setup_class()

    def test_create_task(self):
        rsp = ImageSynthesis.call(model=ImageSynthesis.Models.wanx_v1,
                                  prompt='cute kitten puppy',
                                  n=2)
        assert rsp.status_code == HTTPStatus.OK
        assert rsp.output['task_status'] == 'SUCCEEDED'
        assert len(rsp.output['results']) == 2

    def test_fetch_status(self):
        rsp = ImageSynthesis.call(model=ImageSynthesis.Models.wanx_v1,
                                  prompt='cute kitten puppy',
                                  n=2)
        assert rsp.status_code == HTTPStatus.OK

        rsp = ImageSynthesis.fetch(rsp)
        assert rsp.status_code == HTTPStatus.OK

    def test_wait(self):
        rsp = ImageSynthesis.async_call(model=ImageSynthesis.Models.wanx_v1,
                                        prompt='cute kitten puppy',
                                        n=1)
        assert rsp.status_code == HTTPStatus.OK

        rsp = ImageSynthesis.wait(rsp)
        assert rsp.status_code == HTTPStatus.OK
        assert rsp.output.task_id != ''  # verify access by properties.
        assert rsp.output.task_status == TaskStatus.SUCCEEDED
        assert len(rsp.output.results) == 1
        assert rsp.output.results[0].url != ''

        assert rsp.output['task_id'] != ''
        assert rsp.output['task_status'] == TaskStatus.SUCCEEDED
        assert len(rsp.output['results']) == 1
        assert rsp.output['results'][0]['url'] != ''

    def test_list_cancel_task(self):
        rsp = ImageSynthesis.list(status='CANCELED')
        assert rsp.status_code == HTTPStatus.OK

    def test_list_all(self):
        rsp = ImageSynthesis.list()
        assert rsp.status_code == HTTPStatus.OK
        print(rsp)
