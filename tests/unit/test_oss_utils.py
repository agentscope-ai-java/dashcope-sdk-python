# -*- coding: utf-8 -*-
# Copyright (c) Alibaba, Inc. and its affiliates.

from http import HTTPStatus

from dashscope.utils import oss_utils
from dashscope.utils.oss_utils import OssUtils


class FakeUploadResponse:
    status_code = HTTPStatus.OK
    headers = {}


class FakeSession:
    captured_file = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def post(self, url, files, data, headers, timeout):
        assert url == "https://oss.example.com"
        assert data["key"] == "test-dir/dogs.jpg"
        assert headers["Accept"] == "application/json"
        assert timeout == 3600

        FakeSession.captured_file = files["file"]
        assert not FakeSession.captured_file.closed
        return FakeUploadResponse()


class TestOssUtils:
    def test_upload_closes_opened_file(self, monkeypatch):
        upload_certificate = {
            "oss_access_key_id": "access-key-id",
            "signature": "signature",
            "policy": "policy",
            "upload_dir": "test-dir",
            "x_oss_object_acl": "private",
            "x_oss_forbid_overwrite": "true",
            "upload_host": "https://oss.example.com",
        }
        FakeSession.captured_file = None
        monkeypatch.setattr(oss_utils.requests, "Session", FakeSession)

        file_url, returned_certificate = OssUtils.upload(
            model="test-model",
            file_path="tests/data/dogs.jpg",
            api_key="test-api-key",
            upload_certificate=upload_certificate,
        )

        assert file_url == "oss://test-dir/dogs.jpg"
        assert returned_certificate is upload_certificate
        assert FakeSession.captured_file is not None
        assert FakeSession.captured_file.closed
