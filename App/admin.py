from django.contrib import admin
from App.models import *


class MyUserAdmin(admin.ModelAdmin):
    list_display = ('user_type', 'email', 'mobile', 'first_name', 'last_name', "gender","age", "otp")  
    list_filter = ('created_at',) 
    search_fields = ('first_name',)  
    ordering = ('-created_at',)  
admin.site.register(MyUser, MyUserAdmin)


class ProductAdmin(admin.ModelAdmin):
    list_display = ('title','disc','product_image','category','price')
    list_filter = ('created_at',) 
    search_fields = ('title',)  
    ordering = ('-created_at',)  
admin.site.register(ProductModel, ProductAdmin)


class UserCartAdmin(admin.ModelAdmin):
    list_display = ('cart_user','cart_products','quantity')
    list_filter = ('created_at',) 
    search_fields = ('quantity',)  
    ordering = ('-created_at',)  
admin.site.register(UserCartModel, UserCartAdmin)
