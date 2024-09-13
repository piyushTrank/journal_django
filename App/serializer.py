from rest_framework import serializers
from App.models import *
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .models import MyUser

class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate(self, data):
        email = data.get('email')
        otp = data.get('otp')
        new_password = data.get('new_password')

        try:
            user = MyUser.objects.get(email=email)
        except MyUser.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")

        if user.otp != otp:
            raise serializers.ValidationError("Invalid OTP.")

        return {
            'user': user,
            'new_password': new_password
        }


  


class SignupSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True, validators=[validate_password])
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)

    class Meta:
        model = MyUser
        fields = ['first_name', 'last_name', 'email', 'password']

    def validate(self, attrs):
        unknown_fields = set(attrs) - set(self.fields)
        if unknown_fields:
            raise serializers.ValidationError(f"Unknown field(s): {', '.join(unknown_fields)}")
        return attrs

    def create(self, validated_data):
        email = validated_data.pop('email').lower()
        if MyUser.objects.filter(email=email).exists():
            raise serializers.ValidationError({"message":"User with this email already exists."})

        password = validated_data.pop('password')
        user = MyUser(
            is_active=True,
            email=email,
            user_type="Client",
            **validated_data
        )
        user.set_password(password)
        user.save()
        return user
        


class GetMyUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyUser
        fields = "__all__"
        read_only_fields = ['id', 'email']


class MyUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyUser
        fields = ['first_name', 'last_name', 'email']
        read_only_fields = ['email']

    def update(self, instance, validated_data):
        if 'first_name' in validated_data and validated_data['first_name'] != '':
            instance.first_name = validated_data['first_name']
        if 'last_name' in validated_data and validated_data['last_name'] != '':
            instance.last_name = validated_data['last_name']

        instance.save()
        return instance
    


class UserCartSerializer(serializers.ModelSerializer):
        model = UserCartModel
        fields = [
            'id',
            'name',
            'heading',
            'desc',
            'size',
            'quantity',
            'board_selected',
            'cover_img',
            'inner_img',
            'cart_type',
            'cart_price',
        ]


    



    




