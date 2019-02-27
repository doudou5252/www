from django.shortcuts import render, redirect
from django.urls import reverse  # 反向解析
from django.views.generic import View  # 通过类来进行视图的跳转
from django.contrib.auth import authenticate, login, logout  # 登录校验
from django.http import HttpResponse  # 引入响应
from django.conf import settings  # 引入settings文件
from django.core.mail import send_mail  # 发送邮件


from user.models import User, Address   # 用户模型类
from goods.models import GoodsSKU
from celery_tasks.tasks import send_register_active_email  # 引入发邮件的函数
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer  # 验证激活的
from itsdangerous import SignatureExpired # 验证激活的
from utils.mixin import LoginRequiredMixin
from django_redis import get_redis_connection
import re  # 正则
# Create your views here.


# /user/logout
class LogoutView(View):
    '''退出登录'''
    def get(self, request):
        '''退出登录'''
        # 清除用户的session信息
        logout(request)

        # 跳转到首页
        return redirect(reverse('goods:index'))


# /user
class UserInfoView(LoginRequiredMixin, View):
    '''用户中心-信息页'''
    def get(self, request):
        '''显示'''
        # Django会给request对象添加一个属性request.user
        # 如果用户未登录->user是AnonymousUser类的一个实例对象
        # 如果用户登录->user是User类的一个实例对象
        # request.user.is_authenticated()

        # 获取用户的个人信息
        user = request.user
        address = Address.objects.get_default_address(user)

        # 获取用户的历史浏览记录
        # from redis import StrictRedis
        # sr = StrictRedis(host='172.16.179.130', port='6379', db=9)
        con = get_redis_connection('default')

        history_key = 'history_%d'%user.id

        # 获取用户最新浏览的5个商品的id
        sku_ids = con.lrange(history_key, 0, 4) # [2,3,1]

        # 从数据库中查询用户浏览的商品的具体信息
        # goods_li = GoodsSKU.objects.filter(id__in=sku_ids)
        #
        # goods_res = []
        # for a_id in sku_ids:
        #     for goods in goods_li:
        #         if a_id == goods.id:
        #             goods_res.append(goods)

        # 遍历获取用户浏览的商品信息
        goods_li = []
        for id in sku_ids:
            goods = GoodsSKU.objects.get(id=id)
            goods_li.append(goods)

        # 组织上下文
        context = {'page':'user',
                   'address':address,
                   'goods_li':goods_li}

        # 除了你给模板文件传递的模板变量之外，django框架会把request.user也传给模板文件
        return render(request, 'user_center_info.html', context)


# /user/order
class UserOrderView(LoginRequiredMixin, View):
    '''用户中心-订单页'''
    def get(self, request):
        '''显示'''
        # 获取用户的订单信息

        return render(request, 'user_center_order.html', {'page':'order'})


# /user/address
class AddressView(LoginRequiredMixin, View):
    '''用户中心-地址页'''
    def get(self, request):
        '''显示'''
        # 获取登录用户对应User对象
        user = request.user

        # 获取用户的默认收货地址
        # try:
        #     address = Address.objects.get(user=user, is_default=True) # models.Manager
        # except Address.DoesNotExist:
        #     # 不存在默认收货地址
        #     address = None
        address = Address.objects.get_default_address(user)

        # 使用模板
        return render(request, 'user_center_site.html', {'page':'address', 'address':address})

    def post(self, request):
        '''地址的添加'''
        # 接收数据
        receiver = request.POST.get('receiver')
        addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')

        # 校验数据
        if not all([receiver, addr, phone]):
            return render(request, 'user_center_site.html', {'errmsg':'数据不完整'})

        # 校验手机号
        if not re.match(r'^1[3|4|5|7|8][0-9]{9}$', phone):
            return render(request, 'user_center_site.html', {'errmsg':'手机格式不正确'})

        # 业务处理：地址添加
        # 如果用户已存在默认收货地址，添加的地址不作为默认收货地址，否则作为默认收货地址
        # 获取登录用户对应User对象
        user = request.user

        # try:
        #     address = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        #     # 不存在默认收货地址
        #     address = None

        address = Address.objects.get_default_address(user)

        if address:
            is_default = False
        else:
            is_default = True

        # 添加地址
        Address.objects.create(user=user,
                               receiver=receiver,
                               addr=addr,
                               zip_code=zip_code,
                               phone=phone,
                               is_default=is_default)

        # 返回应答,刷新地址页面
        return redirect(reverse('user:address')) # get请求方式

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
        token = serializer.dumps(info)  # bytes  字节流的数据
        token = token.decode()  # 默认解码utf8

        # 发邮件
        send_register_active_email.delay(email, username, token)

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

        # 业务处理:登录校验  认证系统  User.objects.get(username=username,password=password)
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
                    response.set_cookie('username', username, max_age=7*24*3600)
                else:
                    response.delete_cookie('username')

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
        # serializer = Serializer(settings.SECRET_KEY, 3600)  # 3600 为过期时间
        try:
            # info = serializer.loads(token)
            # # 获取待激活用户的id
            # user_id = info['confirm']

            # 根据id获取用户信息
            user = User.objects.get(id=token)
            user.is_active = 1
            user.save()

            # 跳转到登录页面
            return redirect(reverse('user:login'))
        except SignatureExpired as e:
            # 激活链接已过期
            return HttpResponse('激活链接已过期')
# usr/register
# def register(request):
#     '''显示注册页面'''
#     return render(request, 'register.html')
#
# def register_handle(request):
#     '''进行注册的处理'''
#     # 接受数据
#     username = request.POST.get('user_name')
#     password = request.POST.get('pwd')
#     email = request.POST.get('email')
#     allow = request.POST.get('allow')
#
#     # 进行数据校验
#     if not all([username, password, email]):
#         # 判断是否完整
#         return render(request, 'register.html', {'errmsg': '数据不完整'})
#     if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
#         return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})
#     if allow != 'on':
#         return render(request, 'register.html', {'errmsg': '请同意协议'})
#     # 进行业务处理 进行注册
#     # 以前的逻辑
#     # user = User()
#     # user.username = username
#     # user.password = password
#     # user.email = email
#     # user.allow = allow
#     # user.save()
#
#     user = User.objects.create_user(username, email, password)
#     user.is_active = 0
#     user.save()
#     # 返回应答 跳转到首页
#     return redirect(reverse('goods:index'))  # 注册成功,反向解析,跳转到首页
#




