from django.shortcuts import render, redirect
from django.urls import reverse  # 反向解析
from django.views.generic import View  # 通过类来进行视图的跳转
from django.contrib.auth import authenticate, login  # 登录校验
from django.http import HttpResponse  # 引入响应
from django.conf import settings  # 引入settings文件
from django.core.mail import send_mail  # 发送邮件


from user.models import User   # 用户模型类
# from celery_tasks.tasks import send_register_active_email  # 引入发邮件的函数
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer  # 验证激活的
from itsdangerous import SignatureExpired # 验证激活的
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

        # 加密用户的身份信息，生成激活token
        serializer = Serializer(settings.SECRET_KEY, 3600)
        info = {'confirm': user.id}
        token = serializer.dumps(info)  # bytes
        token = token.decode()

        # 发邮件
        subject = '我是豆豆'  # 邮件标题
        message = '邮件正文'  #
        sender = settings.EMAIL_FROM
        receiver = [email]
        send_mail(subject, message, sender, receiver)

        # send_register_active_email.delay(email, username, token)

        # 返回应答 跳转到首页
        return redirect(reverse('goods:index'))  # 注册成功,反向解析,跳转到首页

# /usr/login
class LoginView(View):
    '''登录'''
    def get(self, request):
        '''显示登录的页面'''
        # 判断是否记住了用户名
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checked = 'cheched'
        else:
            username = ''
            checked = ''

        # 使用模版

        return render(request, 'login.html', {'username': username, 'cheched': checked})
    def post(self, request):
        '''登录校验'''
        # 接受数据
        username = request.POST.get('username')
        password = request.POST.get('pwd')

        # 校验数据
        if not all([username, password]):
            return render(request, 'login.html', {'errmsg': '数据不完整'})

        # 业务处理:登录校验
        user = authenticate(username=username, password=password)
        if user is not None:
            # 用户名密码输入正确
            if user.is_active:
                # 用户名已激活
                # 记录用户的登录状态
                login(request, user)

                # 跳转至首页
                response = redirect(reverse('goods:index'))  # HttpResponseRedirect

                # 判断是否需要记住用户名
                remember = request.POST.get('remember')

                if remember == 'on':
                    # 记住用户名
                    request.set_cookie('username', username, max_age=7*24*3600)
                else:
                    request.delete_cookie('username')

                # 返回 response
                return response
            else:
                # 用户未激活
                return render(request, 'login.html', {'errmsg': '账号未激活'})
        else:
            # 用户名或者密码错误
            return render(request, 'login.html', {'errmsg': '用户名或密码错误'})

# usr/active
class ActiveView(View):
    '''用户激活'''
    def get(self, request, token):
        '''进行用户激活'''
        # 进行解密，获取要激活的用户信息
        serializer = Serializer(settings.SECRET_KEY, 3600)  # 3600 为过期时间
        try:
            info = serializer.loads(token)
            # 获取待激活用户的id
            user_id = info['confirm']

            # 根据id获取用户信息
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()

            # 跳转到登录页面
            return redirect(reverse('user:login'))
        except SignatureExpired as e:
            # 激活链接已过期
            return HttpResponse('激活链接已过期')
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





