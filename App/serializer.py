from rest_framework import serializers
from App.models import *

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
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)

    class Meta:
        model = MyUser
        fields = ['first_name','last_name', 'email', 'password']
        extra_kwargs = {
            'email': {'required': True}, }
    def validate_password(self, value):
        if not value:
            raise serializers.ValidationError("Password is required")
    
        if len(value) < 6 or len(value) > 50:
            raise serializers.ValidationError("The length should be between 6 and 50 characters.")
        return value
    
    def validate(self, attrs):
        unknown_fields = set(self.initial_data) - set(self.fields)
        if unknown_fields:
            raise serializers.ValidationError(f"Unknown field(s): {', '.join(unknown_fields)}")
        return attrs

    def create(self, validated_data):
        email = validated_data.pop('email').lower()
        print("------------------->",email)
        if MyUser.objects.filter(email=email).exists():
            raise serializers.ValidationError("User with this email already exists.")

        password = validated_data.pop('password')
        try:
            user = MyUser(is_active=True,email=email, user_type="Client",**validated_data)
            user.set_password(password)
            user.save()

            return user
        except Exception as e:
            print(e)
            raise serializers.ValidationError("Failed to create user")
        


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
    




