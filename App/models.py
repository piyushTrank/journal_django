from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.db import models
from App.choices import *
import uuid
import datetime
import random
import jwt
from Journal.settings import *
from django.utils import timezone
from django.conf import settings


class CommonTimePicker(models.Model):
    created_at = models.DateTimeField("Created Date", auto_now_add=True)
    updated_at = models.DateTimeField("Updated Date", auto_now=True)

    class Meta:
        abstract = True


class MyUserManager(BaseUserManager):

    def create_user(self, email, password):
        if not email:
            raise ValueError('Users must have an Email Address')

        user = self.model(
            email=self.normalize_email(email),
            is_active=False,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        user = self.model(email=email)
        user.set_password(password)
        user.is_superuser = True
        if user.is_superuser:
            user.first_name = "Admin"
        user.is_active = True
        user.is_staff = True
        user.save(using=self._db)
        return user


class MyUser(AbstractBaseUser,CommonTimePicker):
    user_type = models.CharField("User Type", max_length=10, default='Admin', choices=USERTYPE)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    email = models.EmailField("Email Address", null=True, blank=True, unique=True,db_index=True)
    mobile = models.CharField('Mobile Number', max_length=256,default="",null=True,blank=True)
    first_name = models.CharField("First Name", max_length=256, blank=True, null=True)
    last_name = models.CharField("Last Name", max_length=256, blank=True, null=True)
    avatar = models.ImageField("profile photo", null=True, blank=True,upload_to='user_images')
    gender = models.CharField("Gender", max_length=256, blank=True)
    age = models.DateField("Age", blank=True, null= True)
    otp = models.CharField('OTP', max_length=4, blank=True, null=True)

    is_superuser = models.BooleanField("Super User", default=False)
    is_staff = models.BooleanField("Staff", default=False)
    is_active = models.BooleanField("Active", default=False)
    email_verify = models.BooleanField("Email Verify", default=False)
    is_notification_on=models.BooleanField("is_notification_on",default=True)
    
    objects = MyUserManager()
    USERNAME_FIELD = 'email'
    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return f"{self.uuid}_{self.email}" 
    
    def has_perm(self, perm, obj=None):
        return self.is_staff

    def has_module_perms(self, app_label):
        return self.is_superuser

    def get_short_name(self):
        return self.email

    def otp_creation(self):
        otp = random.randint(1000, 9999)
        self.otp = otp
        self.save()
        return otp
    

class ProductCategoryModel(CommonTimePicker):
    title = models.CharField("Title",max_length=100, null=True,blank=True)
    image = models.ImageField("Image", null=True, blank=True,upload_to='image')
    p_category = models.CharField("Category", max_length=50, choices=PRODUCT_CATEGORY)
    class Meta:
        verbose_name = "Product Category"
        verbose_name_plural = "Product Categorys"

    def __str__(self) -> str:
        return self.p_category

class ProductModel(CommonTimePicker):
    title = models.CharField("Title",max_length=100, null=True,blank=True)
    disc = models.CharField("Disc",max_length=1000, null=True,blank=True)
    product_image = models.ImageField("Product Image", null=True, blank=True,upload_to='product_image')
    category = models.CharField("Category",max_length=20, default='JournalBooks', choices=CATEGORY)
    price = models.PositiveIntegerField("Price",default=0, blank=True, null=True)
    popularity = models.IntegerField("Popularity",default=0,null=True,blank=True)
    color = models.CharField("Color Type", max_length=20, null=True,blank=True)
    lined_non_lined = models.CharField("Lined non Lined", max_length=10, default='All', choices=LINED_NON_LINED)
    cover_type = models.CharField("Cover Type", max_length=20, default='All', choices=COVER_TYPE)
    cover_img = models.ImageField("Cover Image", null=True, blank=True,upload_to='cover_image')
    inner_img = models.ImageField("Inner Image", null=True, blank=True,upload_to='inner_image')
    category_type = models.ForeignKey(ProductCategoryModel, on_delete=models.CASCADE, related_name='category_type')
    additional_price = models.PositiveIntegerField("Additional Price",default=0, blank=True, null=True)
    phrase_flag = models.BooleanField(default=True)
    initial_flag = models.BooleanField(default=True)
    cover_logo_flag = models.BooleanField(default=True)
    inner_text_flag = models.BooleanField(default=True)
    inner_logo_flag = models.BooleanField(default=True)
    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"

    def save(self, *args, **kwargs):
        if self.color:
            self.color = self.color.capitalize()
        super(ProductModel, self).save(*args, **kwargs)

    def __str__(self):
        return self.title

class ProductSizeModel(CommonTimePicker):
    size_user = models.ForeignKey(ProductModel, on_delete=models.CASCADE, related_name='size_user')
    image = models.ImageField("Image", null=True, blank=True,upload_to='image')
    product_size = models.CharField("Product size", max_length=100,null=True,blank=True)

    class Meta:
        verbose_name = "Product Size"
        verbose_name_plural = "Product Sizes"

class UserCartModel(CommonTimePicker):
    cart_user = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name="cart_user")
    cart_products = models.ForeignKey(ProductModel, on_delete=models.CASCADE, related_name="cart_products",blank=True,null=True)
    product_size_user = models.ForeignKey(ProductSizeModel, on_delete=models.CASCADE,related_name='product_size_user',blank=True,null=True)
    name = models.CharField("Name", max_length=100,null=True,blank=True)
    heading = models.CharField("Heading", max_length=100,null=True,blank=True)
    description = models.CharField("Description", max_length=1000,null=True,blank=True)
    currentSize = models.CharField("Size", max_length=100,null=True,blank=True)
    quantity = models.PositiveIntegerField(default=1)
    boardSelectedOption = models.CharField("Board Selected",max_length=20,choices=BOARD_SELECTED)
    cover = models.ImageField("Cover Image", null=True, blank=True,upload_to='edit_cover_img')
    inner = models.ImageField("Inner Image", null=True, blank=True,upload_to='edit_cover_img')
    price = models.PositiveIntegerField("Price",default=0, blank=True, null=True)
    total_price = models.PositiveIntegerField("Total Price",default=0, blank=True, null=True)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = "User Cart"
        verbose_name_plural = "User Carts"
        

    def __str__(self) -> str:
        return self.name
    
class PersentModel(CommonTimePicker):
    quantity = models.PositiveIntegerField("Quantity",default=0, blank=True, null=True)
    persent = models.PositiveIntegerField("Persent",default=0, blank=True, null=True)
    disc = models.CharField("Disc",max_length=1000, null=True,blank=True)
    # def __str__(self):
    #     return self.quantity
    class Meta:
        verbose_name = "Discount"
        verbose_name_plural = "Discounts"


class CouponModel(CommonTimePicker):
    coupon_code = models.CharField(max_length=50, unique=True)
    discount_percentage = models.PositiveIntegerField()
    class Meta:
        verbose_name = "Coupon"
        verbose_name_plural = "Coupons"

    def __str__(self):
        return f"{self.coupon_code}"

    def save(self, *args, **kwargs):
        super(CouponModel, self).save(*args, **kwargs)
        users = MyUser.objects.all()
        for user in users:
            CouponUserModel.objects.create(
                coupon_link=self,
                coupon_user=user
            )
class CouponUserModel(CommonTimePicker):
    coupon_link = models.ForeignKey(CouponModel, on_delete=models.CASCADE, related_name='coupon_link')
    coupon_user = models.OneToOneField(MyUser, on_delete=models.CASCADE, related_name='coupon_user')
    applied = models.BooleanField(default=False)
    class Meta:
        verbose_name = "User linked Coupon"
        verbose_name_plural = "User linked Coupons"

    def __str__(self):
        return f"{self.coupon_user.email} - {self.coupon_link.coupon_code}"




