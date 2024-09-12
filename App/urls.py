from django.urls import path
from App.views import *

urlpatterns = [
    path("login/",LoginAPI.as_view(),name="login"),
    path('reset-password/',ResetPasswordApi.as_view()),
    path('send-otp/',SendOtpApi.as_view()),
    path('signup/',SignupApi.as_view()),
    path('products/',ProductAPi.as_view()),
    path('user-profile/',UserProfileAPI.as_view()),
    path('user-update/',UserUpdateApi.as_view()),
    path('logout/',LogoutUserAPIView.as_view()),
    path('forget-password/',ForgetPasswordAPI.as_view()),
]
