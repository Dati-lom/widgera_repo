from django.contrib.auth.views import LogoutView
from django.urls import path

from .views_web import UserLoginView, UserSignupView

app_name = 'users_web'

urlpatterns = [
    path('signup/', UserSignupView.as_view(), name='signup'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='users_web:login'), name='logout'),
]
