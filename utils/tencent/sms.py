#!/usr/bin/env python
# -*- coding:utf-8 -*-

import ssl
from django.conf import settings

# 避免 SSL 问题
ssl._create_default_https_context = ssl._create_unverified_context

# 只有当 USE_TENCENT_SMS=True 时才导入 SDK
if getattr(settings, "USE_TENCENT_SMS", False):
    from qcloudsms_py import SmsMultiSender, SmsSingleSender
    from qcloudsms_py.httpclient import HTTPError


def send_sms_single(phone_num, template_id, template_param_list):
    """
    单条发送短信
    """
    # 开发/测试模式：用占位实现
    if not getattr(settings, "USE_TENCENT_SMS", False):
        print("=" * 40)
        print("【模拟发送单条短信】")
        print(f"手机号: {phone_num}")
        print(f"模板ID: {template_id}")
        print(f"模板参数: {template_param_list}")
        print("=" * 40)
        return {'result': 0, 'errmsg': "OK (模拟发送成功)"}

    # 生产环境：真实 SDK 调用
    appid = settings.TENCENT_SMS_APP_ID
    appkey = settings.TENCENT_SMS_APP_KEY
    sms_sign = settings.TENCENT_SMS_SIGN
    sender = SmsSingleSender(appid, appkey)
    try:
        response = sender.send_with_param(86, phone_num, template_id, template_param_list, sign=sms_sign)
    except HTTPError:
        response = {'result': 1000, 'errmsg': "网络异常发送失败"}
    return response


def send_sms_multi(phone_num_list, template_id, param_list):
    """
    批量发送短信
    """
    # 开发/测试模式：用占位实现
    if not getattr(settings, "USE_TENCENT_SMS", False):
        print("=" * 40)
        print("【模拟批量发送短信】")
        print(f"手机号列表: {phone_num_list}")
        print(f"模板ID: {template_id}")
        print(f"模板参数: {param_list}")
        print("=" * 40)
        return {'result': 0, 'errmsg': "OK (模拟批量发送成功)"}

    # 生产环境：真实 SDK 调用
    appid = settings.TENCENT_SMS_APP_ID
    appkey = settings.TENCENT_SMS_APP_KEY
    sms_sign = settings.TENCENT_SMS_SIGN
    sender = SmsMultiSender(appid, appkey)
    try:
        response = sender.send_with_param(86, phone_num_list, template_id, param_list, sign=sms_sign)
    except HTTPError:
        response = {'result': 1000, 'errmsg': "网络异常发送失败"}
    return response
