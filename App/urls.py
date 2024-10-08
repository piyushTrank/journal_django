from django.urls import path
from App.views import *

urlpatterns = [
    path("login/",LoginAPI.as_view(),name="login"),
    path('send-otp/',SendOtpApi.as_view()),
    path('signup/',SignupApi.as_view()),
    path('products/',ProductAPi.as_view()),
    path('user-profile/',UserProfileAPI.as_view()),
    path('user-update/',UserUpdateApi.as_view()),
    path('logout/',LogoutUserAPIView.as_view()),
    path('forget-password/',ForgetPasswordAPI.as_view()),
    path('add-to-cart/',AddToCartAPi.as_view()),
    path('get-user-cart/',GetUserCartAPi.as_view()),
    path('cart-remove/', RemoveCartItemAPi.as_view()),
    path('cart-item-in-de/', EncreaseDeCartItemQuantityAPi.as_view()),
    path('our-products/', OurProductsAPi.as_view()),
    path('category-wise-product/', CategoryWiseProduct.as_view()),
    path('product-size/', ProductSizeApi.as_view()),
    path('colors/', SendColorAPi.as_view()),
    path('cart-count/', CartCountApi.as_view()),
    path('discount/', DiscountApi.as_view()),
    path('coupon/', CounponAPi.as_view()),
    path('user-coupons/', GetUserCouponApi.as_view()),
]

