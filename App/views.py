from django.shortcuts import render
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from App.models import *
from rest_framework.exceptions import APIException
from App.serializer import *
from App.email import *
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth.hashers import make_password

class LoginAPI(APIView):
    def post(self, request):
        try:
            user = MyUser.objects.filter(email=request.data.get("email")).first()
            if not user:
                return Response({"message": "User does not exist."}, status=status.HTTP_404_NOT_FOUND)
            if user.user_type == "Admin":
                return Response({"success": False, "message": "Invalid user type."}, status=status.HTTP_400_BAD_REQUEST)
            refresh = RefreshToken.for_user(user)
            token = {
                'access': str(refresh.access_token),
            }
            return Response({
                'responsecode': status.HTTP_200_OK,
                'userid': user.uuid,
                'token': token,
                'responsemessage': 'User logged in successfully.'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Login error: {e}")
            return Response({"success": False, "message": "Something went wrong."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class ResetPasswordApi(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            if "user_id" in request.data and request.data["user_id"] != "":
                user = MyUser.objects.filter(id=request.data["user_id"]).first()
            current_password = serializer.validated_data.get('current_password')
            new_password = serializer.validated_data.get('new_password')

            if not user.check_password(current_password):
                raise APIException("Current password is incorrect.", code=status.HTTP_400_BAD_REQUEST)
            
            user.change_password = False
            user.set_password(new_password)
            user.save() 

            return Response({'responsecode': status.HTTP_200_OK, 'responsemessage': 'Password changed successfully'},)
        else:
            responcemessage = ""
            for item in serializer.errors.items():
                responcemessage += " " + f"error in {item[0]}:-{item[1][0]}"
            response = {
                "responsecode": status.HTTP_400_BAD_REQUEST,
                "responcemessage": responcemessage
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        

class SendOtpApi(APIView):
    def post(self, request):
        try:
            data = request.data
            email = data.get("email")
            if not email:
                return Response({"message": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)
            user = MyUser.objects.filter(email=email).first()
            if not user:
                return Response({"message": "User does not exist."}, status=status.HTTP_404_NOT_FOUND)
            otp = user.otp_creation()
            if send_otp_email(email, otp):
                return Response({"message": "OTP sent successfully."}, status=status.HTTP_200_OK)
            else:
                return Response({"message": "Failed to send OTP. Please try again."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            print(f"Error sending OTP: {e}")
            return Response({"message": "An error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# forget password 

class SignupApi(APIView):
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.save()
            except serializers.ValidationError as e:
                error_detail = e.detail
                return Response(
                    {"responsecode": 400, "responsemessage": error_detail[0]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            refresh = RefreshToken.for_user(user)
            token = {
                'access': str(refresh.access_token)     
            }
            message = {
                "responsecode":status.HTTP_200_OK,
                "responsemessage": "User created successfully. An OTP has been sent to your email for verification.",
                "userid":user.uuid,
                "token":token}
            return Response(message, status=status.HTTP_201_CREATED)
        else:
            responcemessage = ""
            for item in serializer.errors.items():
                responcemessage += " " + f"error in {item[0]}:-{item[1][0]}"
            response = {
                "responsecode": status.HTTP_400_BAD_REQUEST,
                "responcemessage": responcemessage
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        



class ProductAPi(APIView):
    pagination_class = PageNumberPagination
    # permission_classes = [IsAuthenticated]
    def get(self, request):
        from_date = request.query_params.get('from_date')
        to_date = request.query_params.get('to_date')
        sort_by = request.query_params.get('sort_by', None) 
        color = request.query_params.get('color', None)
        lined_non_lined = request.query_params.get('lined_non_lined', None)
        cover_type = request.query_params.get('cover_type', None)

        product_obj = ProductModel.objects.values(
            'id', 'title', 'disc', 'product_image', 'category', 'price', 'popularity', "created_at", 
            "color", "lined_non_lined", "cover_type"
        )
        if from_date and to_date:
            from_date_obj = timezone.datetime.strptime(from_date, '%Y-%m-%d').replace(hour=0, minute=0, second=0, microsecond=0)
            to_date_obj = timezone.datetime.strptime(to_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59, microsecond=999999)
            product_obj = product_obj.filter(created_at__gte=from_date_obj, created_at__lte=to_date_obj)

        if color:
            product_obj = product_obj.filter(color=color)

        if lined_non_lined:
            product_obj = product_obj.filter(lined_non_lined=lined_non_lined)

        if cover_type:
            product_obj = product_obj.filter(cover_type=cover_type)

        if sort_by == 'price_low_to_high':
            product_obj = product_obj.order_by('price')  
        elif sort_by == 'price_high_to_low':
            product_obj = product_obj.order_by('-price') 
        elif sort_by == 'popularity':
            product_obj = product_obj.order_by('-popularity')
        elif sort_by == 'latest':
            product_obj = product_obj.order_by('-id')
        # elif 

        paginator = self.pagination_class()
        paginated_product = paginator.paginate_queryset(product_obj, request)
        response = paginator.get_paginated_response(paginated_product)
        response.data['current_page'] = paginator.page.number  
        response.data['total'] = paginator.page.paginator.num_pages

        return response
    


class UserProfileAPI(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        serializer = GetMyUserSerializer(user)
        data_to_send = {
            "responsemessage":"data getting sucessfully",
            "data":{**serializer.data},
        }
        return Response(data_to_send, status=status.HTTP_200_OK)
    



class UserUpdateApi(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MyUserSerializer

    def put(self, request):
        instance = request.user  
        serializer = self.serializer_class(instance, data=request.data, partial=True)
        
        if 'current_password' in request.data and 'new_password' in request.data:
            if not instance.check_password(request.data['current_password']):
                return Response({"message": "Current password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)
            instance.set_password(request.data['new_password'])
        
        if serializer.is_valid():
            serializer.save() 
            if 'current_password' in request.data and 'new_password' in request.data:
                instance.save()  # Save password changes
            serialized_data = self.serializer_class(instance).data
            data = {
                "userid": request.user.id,
                "responsecode": status.HTTP_200_OK,
                "responsemessage": "User profile updated successfully",
                "serialized_data": serialized_data
            }
            return Response(data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class LogoutUserAPIView(APIView):
    def post(self, request):
        current_user = MyUser.objects.get(id=request.user.id)
        return Response({"success": True, "message": "Logout user successfully"}, status=status.HTTP_200_OK)
    
  


class ForgetPasswordAPI(APIView):
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data.get('user')
            new_password = serializer.validated_data.get('new_password')

            user.set_password(new_password)
            user.otp = '' 
            user.save()

            return Response({'messagecode': status.HTTP_200_OK, 'message': 'Password reset successfully'}, status=status.HTTP_200_OK)
        else:
            errors = serializer.errors
            responcemessage = ""
            if 'non_field_errors' in errors:
                responcemessage = " ".join(errors['non_field_errors'])
            elif errors:
                responcemessage = " ".join(f"{field}: {msg[0]}" for field, msg in errors.items())
            response = {
                "responsecode": status.HTTP_400_BAD_REQUEST,
                "message": responcemessage or "There was an error processing your request."
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)