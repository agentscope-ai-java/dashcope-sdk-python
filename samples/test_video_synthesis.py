# -*- coding: utf-8 -*-
from http import HTTPStatus
from dashscope import VideoSynthesis
import os

prompt = "一只小猫在月光下奔跑"
audio_url = "https://help-static-aliyun-doc.aliyuncs.com/file-manage-files/zh-CN/20250925/ozwpvi/rap.mp3"
reference_urls = [
    "https://test-data-center.oss-accelerate.aliyuncs.com/wanx/video/resources/with_human_voice_11s.mov",
]
api_key = os.getenv("DASHSCOPE_API_KEY")


def simple_call():
    print("----sync call, please wait a moment----")
    rsp = VideoSynthesis.call(
        api_key=api_key,
        model="wan2.6-r2v",
        reference_urls=reference_urls,
        shot_type="multi",
        audio=True,
        watermark=True,
        prompt=prompt,
    )
    if rsp.status_code == HTTPStatus.OK:
        print("response: %s" % rsp)
    else:
        print(
            "sync_call Failed, status_code: %s, code: %s, message: %s"
            % (rsp.status_code, rsp.code, rsp.message),
        )


def simple_call_t2v():
    print("----sync call, please wait a moment----")
    rsp = VideoSynthesis.call(
        api_key=api_key,
        model="wan2.7-t2v",
        audio=True,
        watermark=True,
        prompt=prompt,
    )
    if rsp.status_code == HTTPStatus.OK:
        print("response: %s" % rsp)
    else:
        print(
            "sync_call Failed, status_code: %s, code: %s, message: %s"
            % (rsp.status_code, rsp.code, rsp.message),
        )

media_i2v = [
    {
        "type": "last_frame",
        "url": "https://wanx.alicdn.com/material/20250318/last_frame.png"
    },
    {
        "type": "first_frame",
        "url": "https://wanx.alicdn.com/material/20250318/first_frame.png"
    },
    {
        "url": "https://test-data-center.oss-accelerate.aliyuncs.com/wanx/audio/mp3_3s.mp3",
        "type": "driven_audio"
    }
]

def simple_call_wan27_i2v():
    print("----sync call, please wait a moment----")
    rsp = VideoSynthesis.call(
        api_key=api_key,
        model="wan2.7-i2v",
        media=media_i2v,
        shot_type="multi",
        audio=True,
        watermark=True,
        prompt=prompt,
    )
    if rsp.status_code == HTTPStatus.OK:
        print("response: %s" % rsp)
    else:
        print(
            "sync_call Failed, status_code: %s, code: %s, message: %s"
            % (rsp.status_code, rsp.code, rsp.message),
        )

media_r2v = [
    {
        "type": "reference_image",
        "url": "https://test-data-center.oss-accelerate.aliyuncs.com/wanx/image/res240_269.jpg"
    },
    {
        "type": "reference_image",
        "url": "https://test-data-center.oss-accelerate.aliyuncs.com/wanx/image/man_5K_7_7K_18_4M.JPG",
        "reference_voice": "https://test-data-center.oss-accelerate.aliyuncs.com/wanx/audio/2s.wav"
    },
    {
        "type": "reference_video",
        "url": "https://test-data-center.oss-accelerate.aliyuncs.com/wanx/video/resources/cast/100M.mov",
        "reference_voice": "https://test-data-center.oss-accelerate.aliyuncs.com/wanx/audio/mp3_1s.mp3"
    },
    {
        "type": "reference_video",
        "url": "https://test-data-center.oss-accelerate.aliyuncs.com/wanx/video/resources/cast/29_99s.mp4",
        "reference_description": "这是一个身穿蓝衣的男子<cast>,他有着浓密的络腮胡"
    },
    {
        "type": "reference_video",
        "url": "https://test-data-center.oss-accelerate.aliyuncs.com/wanx/video/resources/cast/cat_127.mp4",
        "reference_voice": "https://test-data-center.oss-accelerate.aliyuncs.com/wanx/audio/wav_10s.wav",
        "reference_description": "这是一只毛绒小猫<cast>,它正在对着镜头微笑"
    }
]

def simple_call_wan27_r2v():
    print("----sync call, please wait a moment----")
    rsp = VideoSynthesis.call(
        api_key=api_key,
        model="wan2.7-r2v",
        media=media_r2v,
        shot_type="multi",
        audio=True,
        watermark=True,
        prompt=prompt,
    )
    if rsp.status_code == HTTPStatus.OK:
        print("response: %s" % rsp)
    else:
        print(
            "sync_call Failed, status_code: %s, code: %s, message: %s"
            % (rsp.status_code, rsp.code, rsp.message),
        )



if __name__ == "__main__":
    simple_call()
    # simple_call_t2v()
    # simple_call_wan27_i2v()
    # simple_call_wan27_r2v()
