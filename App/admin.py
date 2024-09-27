from django.contrib import admin
from App.models import *


class MyUserAdmin(admin.ModelAdmin):
    list_display = ('user_type', 'email', 'mobile', 'first_name', 'last_name', "gender","age")  
    list_filter = ('created_at',) 
    search_fields = ('first_name',)  
    ordering = ('-created_at',)  
admin.site.register(MyUser, MyUserAdmin)


class ProductAdmin(admin.ModelAdmin):
    list_display = ('title','product_image','category','price','popularity','color','lined_non_lined','cover_type','cover_img','inner_img','category_type__title','phrase_flag','initial_flag','cover_logo_flag','inner_text_flag','inner_logo_flag',)
    list_filter = ('created_at',) 
    search_fields = ('title',)  
    ordering = ('-created_at',)  
admin.site.register(ProductModel, ProductAdmin)


class UserCartAdmin(admin.ModelAdmin):
    list_display = ('cart_user','cart_products','quantity','name','heading','currentSize','quantity','boardSelectedOption','cover','inner','price',)
    list_filter = ('created_at',) 
    search_fields = ('quantity',)  
    ordering = ('-created_at',)  
admin.site.register(UserCartModel, UserCartAdmin)




class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('title','image','p_category',)
    list_filter = ('created_at',) 
    search_fields = ('p_category',)  
    ordering = ('-created_at',)  
admin.site.register(ProductCategoryModel, ProductCategoryAdmin)


class ProductSizeAdmin(admin.ModelAdmin):
    list_display = ('size_user', 'image', 'product_size',)
    list_filter = ('created_at',)
    search_fields = ('product_size'),
    ordering = ('-created_at',) 
admin.site.register(ProductSizeModel, ProductSizeAdmin) 


class PersentAdmin(admin.ModelAdmin):
    list_display = ('persent', 'quantity',)
    list_filter = ('created_at',)
    ordering = ('-created_at',) 
admin.site.register(PersentModel, PersentAdmin) 



class CouponAdmin(admin.ModelAdmin):
    list_display = ('coupon_code', 'discount_percentage',)
    list_filter = ('created_at',)
    ordering = ('-created_at',) 
admin.site.register(CouponModel, CouponAdmin) 


class CouponUserAdmin(admin.ModelAdmin):
    list_display = ('coupon_link', 'coupon_user','applied',)
    list_filter = ('created_at',)
    ordering = ('-created_at',) 
admin.site.register(CouponUserModel, CouponUserAdmin) 
