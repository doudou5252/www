from django.conf.urls import url
from goods import views

app_name = 'goods'
urlpatterns = [
    url(r'^$', views.index, name='index'),  # 首页
]
