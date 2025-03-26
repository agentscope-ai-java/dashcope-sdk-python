# Copyright (c) Alibaba, Inc. and its affiliates.

from http import HTTPStatus

from dashscope import VideoSynthesis
from dashscope.common.constants import TaskStatus
from tests.base_test import BaseTestEnvironment


class TestAsyncVideoSynthesisRequest(BaseTestEnvironment):
    @classmethod
    def setup_class(cls):
        super().setup_class()

    def test_create_task(self):
        rsp = VideoSynthesis.call(
            model=VideoSynthesis.Models.wanx_txt2video_pro,
            prompt='cute kitten puppy')
        assert rsp.status_code == HTTPStatus.OK

        assert rsp.output['task_status'] == 'SUCCEEDED'

    def test_fetch_status(self):
        rsp = VideoSynthesis.call(
            model=VideoSynthesis.Models.wanx_txt2video_pro,
            prompt='cute kitten puppy')
        assert rsp.status_code == HTTPStatus.OK

        rsp = VideoSynthesis.fetch(rsp)
        assert rsp.status_code == HTTPStatus.OK

    def test_wait(self):
        rsp = VideoSynthesis.async_call(
            model=VideoSynthesis.Models.wanx_txt2video_pro,
            prompt='cute kitten puppy')
        assert rsp.status_code == HTTPStatus.OK

        rsp = VideoSynthesis.wait(rsp)
        assert rsp.status_code == HTTPStatus.OK
        assert rsp.output.task_id != ''  # verify access by properties.
        assert rsp.output.task_status == TaskStatus.SUCCEEDED
        assert rsp.output.video_url != ''

        assert rsp.output['task_id'] != ''
        assert rsp.output['task_status'] == TaskStatus.SUCCEEDED
        assert rsp.output['video_url'] != ''

    def test_list_cancel_task(self):
        rsp = VideoSynthesis.list(status='CANCELED')
        assert rsp.status_code == HTTPStatus.OK

    def test_list_all(self):
        rsp = VideoSynthesis.list()
        assert rsp.status_code == HTTPStatus.OK
        print(rsp)
