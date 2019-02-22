from django.shortcuts import render, redirect
from django.urls import reverse  # 反向解析
from django.views.generic import View


from user.models import User   # 用户模型类
import re  # 正则
# Create your views here.

# usr/register
class RegisterView(View):
    '''注册'''
    def get(self, request):
        '''显示页面注册'''
        return render(request, 'register.html')

    def post(self, request):
        '''进行注册处理'''
        # 接受数据
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        # 进行数据校验
        if not all([username, password, email]):
            # 判断是否完整
            return render(request, 'register.html', {'errmsg': '数据不完整'})
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})
        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请同意协议'})
        # 进行业务处理 进行注册
        # 以前的逻辑
        # user = User()
        # user.username = username
        # user.password = password
        # user.email = email
        # user.allow = allow
        # user.save()

        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()
        # 返回应答 跳转到首页
        return redirect(reverse('goods:index'))  # 注册成功,反向解析,跳转到首页
# usr/register
def register(request):
    '''显示注册页面'''
    return render(request, 'register.html')

def register_handle(request):
    '''进行注册的处理'''
    # 接受数据
    username = request.POST.get('user_name')
    password = request.POST.get('pwd')
    email = request.POST.get('email')
    allow = request.POST.get('allow')

    # 进行数据校验
    if not all([username, password, email]):
        # 判断是否完整
        return render(request, 'register.html', {'errmsg': '数据不完整'})
    if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
        return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})
    if allow != 'on':
        return render(request, 'register.html', {'errmsg': '请同意协议'})
    # 进行业务处理 进行注册
    # 以前的逻辑
    # user = User()
    # user.username = username
    # user.password = password
    # user.email = email
    # user.allow = allow
    # user.save()

    user = User.objects.create_user(username, email, password)
    user.is_active = 0
    user.save()
    # 返回应答 跳转到首页
    return redirect(reverse('goods:index'))  # 注册成功,反向解析,跳转到首页



