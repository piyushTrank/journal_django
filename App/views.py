from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from App.models import *
from rest_framework.exceptions import APIException
from App.serializer import *
from App.email import *
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth.hashers import make_password
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from App.utlis import *
from django.db.models import Count
from django.db.models import Prefetch ,Sum, Q

class LoginAPI(APIView):
    def post(self, request):
        try:
            user = MyUser.objects.get(email=request.data.get("email"))
            if user.user_type == "Admin":
                return Response({"success": False, "message": "Invalid user type."}, status=status.HTTP_400_BAD_REQUEST)

        except MyUser.DoesNotExist:
            return Response({"message": "User does not exist."}, status=status.HTTP_404_NOT_FOUND)
        
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
        

class SendOtpApi(APIView):
    def post(self, request):
        try:
            if not request.data["email"]:
                return Response({"message": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)
            user = MyUser.objects.get(email=request.data["email"])
            if not user:
                return Response({"message": "User does not exist."}, status=status.HTTP_404_NOT_FOUND)
            otp = user.otp_creation()
            if send_otp_email(request.data["email"], otp):
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
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            token = {'access': str(refresh.access_token)}
            response = {
                "responsecode": status.HTTP_201_CREATED,
                "responsemessage": "User created successfully.",
                "userid": user.uuid,
                "token": token
            }
            return Response(response, status=status.HTTP_201_CREATED)
        
        # Format error messages
        error_messages = {field: errors[0] for field, errors in serializer.errors.items()}
        response = {
            "responsecode": status.HTTP_400_BAD_REQUEST,
            "responsemessage": error_messages
        }
        return Response(response, status=status.HTTP_400_BAD_REQUEST)
        
# @method_decorator(cache_page(60 * 15), name='get')
from django.db.models import OuterRef, Subquery

class ProductAPi(APIView):
    pagination_class = PageNumberPagination
    def post(self, request):
        base_url = request.build_absolute_uri('/')
        data = request.data  
        from_date = data.get('from_date')
        to_date = data.get('to_date')
        sort_by = data.get('sort_by', None)
        colors = data.get('color', [])
        lined_non_lined = data.get('lined_non_lined', [])
        cover_type = data.get('cover_type', [])
        title = data.get('title')
        category = data.get('category')
        category_counts = ProductModel.objects.values('category_type__category').annotate(count=Count('category_type__category'))

        product_obj = ProductModel.objects.select_related('category_type__category').all()
        category_obj = ProductCategoryModel.objects.filter(category=category).annotate(
            first_product_id=Subquery(
                ProductModel.objects.filter(category_type=OuterRef('pk')).order_by('id').values('id')[:1]
            ),
            first_product_price=Subquery(
                ProductModel.objects.filter(category_type=OuterRef('pk')).order_by('id').values('price')[:1]
            )
        ).values('title', 'image', 'p_category', 'category', 'first_product_price', 'first_product_id')
        default = False
        if from_date and to_date:
            from_date_obj = timezone.datetime.strptime(from_date, '%Y-%m-%d').replace(hour=0, minute=0, second=0, microsecond=0)
            to_date_obj = timezone.datetime.strptime(to_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59, microsecond=999999)
            product_obj = product_obj.filter(created_at__gte=from_date_obj, created_at__lte=to_date_obj)
        
        if category:
            product_obj = product_obj.filter(category_type__category=category)
        if colors:
            product_obj = product_obj.filter(color__in=colors)
            default=True
        if lined_non_lined:
            product_obj = product_obj.filter(lined_non_lined__in=lined_non_lined)
            default=True
        if cover_type:
            product_obj = product_obj.filter(cover_type__in=cover_type)
            default=True
        if title:
            product_obj = product_obj.filter(title__icontains=title)
            default=True
        if sort_by == 'price_low_to_high':
            product_obj = product_obj.order_by('price')
            default=True
        elif sort_by == 'price_high_to_low':
            product_obj = product_obj.order_by('-price')
            default=True
        elif sort_by == 'popularity':
            product_obj = product_obj.order_by('-popularity')
            default=True
        elif sort_by == 'latest':
            product_obj = product_obj.order_by('-id')
            default=True
        if not default:
            category_parent_counts = ProductCategoryModel.objects.values('category').annotate(count=Count('category'))
            for item in category_obj:
                if item['image']:
                    item['image'] = f"{base_url.rstrip('/')}/media/{item['image']}"
            category_counts = {}
            for obj in category_parent_counts:
                category_counts[obj['category']] = obj['count']
            return Response({"results": category_obj,"count": category_obj.count(),"category_counts": category_counts,"status": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        product_obj = product_obj.values(
            'id', 'title', 'disc', 'product_image', 'price', 'popularity',
            'color', 'lined_non_lined', 'cover_type', 'created_at',
            'category_type__title', 'category_type__image', 'category_type__p_category'
        )
        for item in product_obj:
            if item['product_image']:
                item['product_image'] = f"{base_url.rstrip('/')}/media/{item['product_image']}"

        paginator = self.pagination_class()
        paginated_product = paginator.paginate_queryset(product_obj, request)
        response = paginator.get_paginated_response(paginated_product)

        response.data['category_counts'] = {category['category_type__category']: category['count'] for category in category_counts}
        response.data['current_page'] = paginator.page.number
        response.data['total_pages'] = paginator.page.paginator.num_pages
        return response
    

# @method_decorator(cache_page(60 * 15), name='get')
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
                instance.save()  
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
        



class AddToCartAPi(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user = request.user
        customise_price = request.data.get('customise_price')
        product_id = request.data.get('product_id', None)
        base_url = request.build_absolute_uri('/').rstrip('/')
        current_size_id = request.data.get('currentSize')
        quantity = int(request.data.get('quantity', 1))
        page_count = int(request.data.get('page_count', 200))
        final_price = 0
        product_price = 0
        if product_id:
            try:
                product_obj = ProductModel.objects.get(id=product_id)
                product_obj.page_count = page_count
                product_obj.save()
                additional_price = product_obj.additional_price
                product_price = product_obj.price or 0
                final_price = additional_price + product_price if customise_price == "Yes" else product_price
            except ProductModel.DoesNotExist:
                return Response({"error": "Invalid product ID"}, status=status.HTTP_404_NOT_FOUND)
        else:
            product_obj = None

        cover_image = base64_to_image(request.data.get('cover'), "cover_img.png") if request.data.get('cover') else None
        inner_image = base64_to_image(request.data.get('inner'), "inner_img.png") if request.data.get('inner') else None
        if current_size_id != 'default':
            try:
                product_size_obj = ProductSizeModel.objects.get(id=current_size_id)
            except ProductSizeModel.DoesNotExist:
                return Response({"error": "Invalid size ID"}, status=status.HTTP_404_NOT_FOUND)
        else:
            product_size_obj = None

        discount_percentage = 0
        try:
            persent_entry = PercentModel.objects.filter(Q(min_qty__lte=quantity) & Q(max_qty__gt=quantity)).first()
            if not persent_entry and PercentModel.objects.exists():
                persent_entry = PercentModel.objects.filter(max_qty__lt=quantity).order_by('-max_qty').first()

            discount_percentage = int(persent_entry.persent) if persent_entry else 0
        except:
            discount_percentage = 0
        if discount_percentage > 0:
            total_price = final_price * quantity
            discount_amount = total_price * (discount_percentage / 100)
            final_price = total_price - discount_amount
        else:
            final_price = final_price * quantity

        cart_user = UserCartModel.objects.create(
            cart_user=user,
            cart_products=product_obj,
            product_size_user=product_size_obj,
            name=request.data.get('name', ''),
            heading=request.data.get('heading', ''),
            description=request.data.get('description', ''),
            quantity=quantity,
            boardSelectedOption=request.data.get('boardSelectedOption', ''),
            cover=cover_image,
            inner=inner_image,
            price=product_obj.price,
            total_price=final_price
        )
        cart_data = {
            "cart_user": cart_user.cart_user.uuid,
            "quantity": cart_user.quantity,
            "price": cart_user.price,
            "name": cart_user.name,
            "heading": cart_user.heading,
            "description": cart_user.description,
            "currentSize": cart_user.product_size_user.id if cart_user.product_size_user else None,
            "boardSelectedOption": cart_user.boardSelectedOption,
            "cover": f"{base_url}{cart_user.cover.url}" if cart_user.cover else None,
            "inner": f"{base_url}{cart_user.inner.url}" if cart_user.inner else None,
            "discount_applied": f"{discount_percentage}%"
        }
        return Response({"message": "Added to cart successfully", "data": cart_data}, status=status.HTTP_200_OK)




class GetUserCartAPi(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        base_url = request.build_absolute_uri('/')
        cart_items = UserCartModel.objects.filter(cart_user=request.user).values(
            "id","name", "heading", "description", "currentSize", "quantity", "boardSelectedOption", "cover", "inner", "price","total_price"
        )
        total_price_sum = UserCartModel.objects.filter(cart_user=request.user).aggregate(Sum('total_price'))['total_price__sum'] or 0
        for item in cart_items:
            if item['cover']:
                item['cover'] = f"{base_url.rstrip('/')}/media/{item['cover']}"
            if item['inner']:
                item['inner'] = f"{base_url.rstrip('/')}/media/{item['inner']}"
        return Response({"message": "Cart data retrieved successfully", "data": list(cart_items),"total_price_sum":total_price_sum}, status=status.HTTP_200_OK)



class RemoveCartItemAPi(APIView):
    permission_classes = [IsAuthenticated]
    def put(self, request):
        item_id = request.data.get('item_id')
        if not item_id:
            return Response({"message": "Item ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            cart_item = UserCartModel.objects.get(id=item_id, cart_user=request.user)
            cart_item.delete()
            return Response({"message": "Cart item removed successfully"}, status=status.HTTP_204_NO_CONTENT)
        except UserCartModel.DoesNotExist:
            return Response({"message": "Cart item not found"}, status=status.HTTP_404_NOT_FOUND)


 
class EncreaseDeCartItemQuantityAPi(APIView):
    permission_classes = [IsAuthenticated]
    def put(self, request):
        discount_percentage = ''
        item_id = request.data.get('id')
        quantity_obj = request.data.get('quantity')
        if not item_id:
            return Response({"message": "Item ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            cart_item = UserCartModel.objects.get(id=item_id, cart_user=request.user)
            cart_item.quantity = int(quantity_obj)
            cart_item.total_price = cart_item.price * int(quantity_obj)
            try:
                persent_entry = PercentModel.objects.filter(Q(min_qty__lte=cart_item.quantity) & Q(max_qty__gt=cart_item.quantity)).first()
                if not persent_entry and PercentModel.objects.exists():
                    persent_entry = PercentModel.objects.filter(max_qty__lt=cart_item.quantity).order_by('-max_qty').first()
                discount_percentage = int(persent_entry.persent)
                print("discount_percentage",discount_percentage)
                if discount_percentage > 0:
                    cart_item.quantity = int(quantity_obj)
                    original_price = cart_item.price * quantity_obj
                    print("original_price",original_price)
                    discount = original_price * ((100 - discount_percentage) / 100)
                    cart_item.total_price = discount
            except Exception as e:
                print("======",e)
            cart_item.save()

            return Response({
                "message": "Quantity updated successfully",
                "quantity": cart_item.quantity,
                "price": cart_item.price,
                "discount_applied": f"{discount_percentage}%"
            }, status=status.HTTP_200_OK)

        except UserCartModel.DoesNotExist:
            return Response({"message": "Cart item not found"}, status=status.HTTP_404_NOT_FOUND)




class OurProductsAPi(APIView):
    # permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination
    def get(self, request):
        base_url = request.build_absolute_uri('/')
        product_obj = ProductModel.objects.values('id','title','disc','product_image','category_type__category','price','popularity','color','lined_non_lined','cover_type').order_by('?')[:20]
        for item in product_obj:
            if item['product_image']:
                item['product_image'] = f"{base_url.rstrip('/')}/media/{item['product_image']}"
        return Response({"message":"Data getting sucessfully","data":list(product_obj)},status=status.HTTP_200_OK)
    

class CategoryWiseProduct(APIView):
    def get(self, request):
        base_url = request.build_absolute_uri('/')
        product_id = request.query_params.get('product_id')
        try:
            product = ProductModel.objects.get(id=product_id)
            category_type = product.category_type
            related_products = ProductModel.objects.filter(category_type=category_type).values("id","inner_img","cover_img","product_image","title","disc","category_type__category","price","popularity","color","lined_non_lined","cover_type","category_type__title","category_type__image","category_type__p_category", "phrase_flag","initial_flag","cover_logo_flag","inner_text_flag", "inner_logo_flag","additional_price","own_design_flag","inner_own_flag","page_count","page_count","page_count_flag","lined_flag","blank_flag").order_by("-id")
            
            for item in related_products:
                if item['product_image']:
                    item['product_image'] = f"{base_url.rstrip('/')}/media/{item['product_image']}"
                if item['cover_img']:
                    item['cover_img'] = f"{base_url.rstrip('/')}/media/{item['cover_img']}"
                if item['inner_img']:
                    item['inner_img'] = f"{base_url.rstrip('/')}/media/{item['inner_img']}"
                if item['category_type__image']:
                    item['category_type__image'] = f"{base_url.rstrip('/')}/media/{item['category_type__image']}"
            return Response({
                "message": "Data retrieved successfully",
                "related_products": list(related_products)
            }, status=200)
        
        except ProductModel.DoesNotExist:
            return Response({"message": "Product not found"}, status=404)




class ProductSizeApi(APIView):
    def get(self, request):
        base_url = request.build_absolute_uri('/')
        product_id = request.query_params.get('product_id')

        try:
            product = ProductModel.objects.get(id=product_id)
            category_type = product.category_type

            related_products = ProductModel.objects.filter(
                category_type=category_type
            ).prefetch_related(
                Prefetch('size_user', queryset=ProductSizeModel.objects.all())
            )
            sizes = [{
                    'id': size.id,'product_size': size.product_size,'image': f"{base_url.rstrip('/')}/media/{size.image}" if size.image else None
                }
                for product in related_products
                for size in product.size_user.all()
            ]
            return Response({"message": "Data retrieved successfully","data": sizes}, status=200)
        except ProductModel.DoesNotExist:
            return Response({"message": "Product not found"}, status=404)


class SendColorAPi(APIView):
    def get(self, request):
        try:
            colors = ProductModel.objects.values_list("color",flat=True).distinct()
            return Response({"message":"Data getting sucessfully","data":colors},status=status.HTTP_200_OK)
        except: 
            return Response({"message":"Data not found"},status=status.HTTP_404_NOT_FOUND)
        

class CartCountApi(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            cart_count = UserCartModel.objects.filter(cart_user=request.user).count()
            return Response({"message": "Count of cart items.", "count": cart_count}, status=status.HTTP_200_OK)
        except:
            return Response({"message": "Data not found."}, status=status.HTTP_404_NOT_FOUND)


class DiscountApi(APIView):
    def get(self, request):
        try:
            discount = PercentModel.objects.values('min_qty','max_qty','persent','disc')
            return Response({"message":"Data getting sucessfully","Data":list(discount)},status=status.HTTP_200_OK)
        except:
            return Response({"message":"Data not found"},status=status.HTTP_404_NOT_FOUND)


class CounponAPi(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            coupon_code = request.data.get('coupon_code', None)
            if not coupon_code:
                return Response({"error": "Coupon code is required."}, status=status.HTTP_400_BAD_REQUEST)
            try:
                coupon = CouponModel.objects.get(coupon_code=coupon_code, coupon_user=request.user, applied=False)
            except CouponModel.DoesNotExist:
                return Response({"message": "Invalid or already applied coupon."}, status=status.HTTP_400_BAD_REQUEST)
            total_price_sum = UserCartModel.objects.filter(cart_user=request.user).aggregate(Sum('total_price'))['total_price__sum'] or 0
            print("Total cart price:", total_price_sum)
            if total_price_sum < coupon.min_amount:
                return Response({"message": f"Minimum cart amount of {coupon.min_amount} is required to apply this coupon."}, status=status.HTTP_400_BAD_REQUEST)
            discount_amount = coupon.discount_amount
            total_price_after_discount = total_price_sum - discount_amount
            total_price_after_discount = max(total_price_after_discount, 0)
            # coupon.applied = True
            # coupon.save()
            return Response({
                "id":coupon.id,
                "message": "Coupon applied successfully.",
                "original_price": total_price_sum,
                "discount_amount": discount_amount,
                "discount_price": total_price_after_discount
            }, status=status.HTTP_200_OK)

        except ProductModel.DoesNotExist:
            return Response({"message": "Product not found."}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            print(e)
            return Response({"message": "An error occurred while applying the coupon."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetUserCouponApi(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user_coupon = CouponModel.objects.filter(coupon_user=request.user).values('id','coupon_code', 'discount_amount', 'min_amount', 'applied','disc')
        if user_coupon.exists():
            return Response({"message": "Data found.", "data": list(user_coupon)}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "No coupons found for this user."}, status=status.HTTP_404_NOT_FOUND)

