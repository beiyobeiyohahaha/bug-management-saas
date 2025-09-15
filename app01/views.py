# app01/views.py
from django.shortcuts import render, HttpResponse
from django.http import JsonResponse
import random

from django import forms
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.conf import settings

from app01 import models
from utils.tencent.sms import send_sms_single   # 这是你的 mock 短信函数
from utils import redis_pool                    # 这是你写的 redis 封装


# ========== 1) 发送短信 ==========
def send_sms(request):
    """
    GET /app01/send/sms/?phone=手机号&tpl=register
    返回 JSON：{"status":"ok","msg":"验证码已发送","code":1234}  # mock 下会直接回传 code
    """
    tpl = request.GET.get('tpl')
    phone = request.GET.get('phone')

    # 检查参数
    if not phone:
        return JsonResponse({'status': 'error', 'msg': '缺少手机号'})
    if not tpl:
        return JsonResponse({'status': 'error', 'msg': '缺少模板参数 tpl'})

    template_id = settings.TENCENT_SMS_TEMPLATE.get(tpl)
    if not template_id:
        return JsonResponse({'status': 'error', 'msg': '模板不存在'})

    # 生成验证码并存 Redis
    code = random.randint(1000, 9999)
    redis_pool.save_code(phone, code, expire=60)

    # 模拟发送短信（伪代码，不会真的发）
    res = send_sms_single(phone, template_id, [code])
    if res.get('result') == 0:
        return JsonResponse({'status': 'ok', 'msg': '验证码已发送（mock）', 'code': code})
    else:
        return JsonResponse({'status': 'error', 'msg': res.get('errmsg', '发送失败')})


# ========== 2) 注册表单 ==========
class RegisterModelForm(forms.ModelForm):
    mobile_phone = forms.CharField(
        label='手机号',
        validators=[RegexValidator(r'^(1[3-9])\d{9}$', '手机号格式错误')],
    )
    password = forms.CharField(label='密码', widget=forms.PasswordInput())
    confirm_password = forms.CharField(label='重复密码', widget=forms.PasswordInput())
    code = forms.CharField(label='验证码')

    class Meta:
        model = models.UserInfo
        fields = ['username', 'email', 'mobile_phone', 'password', 'confirm_password', 'code']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for _, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = '请输入{}'.format(field.label)

    # 校验两次密码一致
    def clean(self):
        cleaned = super().clean()
        pwd = cleaned.get('password')
        cpwd = cleaned.get('confirm_password')
        if pwd and cpwd and pwd != cpwd:
            self.add_error('confirm_password', '两次密码不一致')
        return cleaned

    # 校验手机号是否已注册
    def clean_mobile_phone(self):
        phone = self.cleaned_data['mobile_phone']
        if models.UserInfo.objects.filter(mobile_phone=phone).exists():
            raise ValidationError('手机号已注册')
        return phone

    # 校验验证码
    def clean_code(self):
        phone = self.cleaned_data.get('mobile_phone')
        code = self.cleaned_data.get('code')
        real_code = redis_pool.get_code(phone)
        if not real_code:
            raise ValidationError('验证码已过期，请重新获取')
        if str(code) != str(real_code):
            raise ValidationError('验证码错误')
        return code


# ========== 3) 注册视图 ==========
def register(request):
    if request.method == 'GET':
        form = RegisterModelForm()
        return render(request, 'app01/register.html', {'form': form})

    # POST 请求
    form = RegisterModelForm(data=request.POST)
    if form.is_valid():
        models.UserInfo.objects.create(
            username=form.cleaned_data['username'],
            email=form.cleaned_data['email'],
            mobile_phone=form.cleaned_data['mobile_phone'],
            password=form.cleaned_data['password'],  # 上线时建议加密
        )
        # 删除验证码
        redis_pool.del_code(form.cleaned_data['mobile_phone'])
        return JsonResponse({'status': 'ok', 'msg': '注册成功'})
    else:
        return JsonResponse({'status': 'error', 'errors': form.errors})

