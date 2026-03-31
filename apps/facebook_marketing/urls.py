from django.urls import path
from . import views

app_name = 'facebook_marketing'

urlpatterns = [
    path('autopost/', views.facebook_autopost_view, name='autopost'),
    path('api/post/', views.api_post_fb, name='api_post'), # API xử lý đăng bài
]