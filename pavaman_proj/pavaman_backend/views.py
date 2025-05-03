
from aiohttp import ClientError
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError
import json
import os
from django.conf import settings
from datetime import datetime,timedelta
import shutil
from django.contrib.sessions.models import Session
import random 
from .sms_utils import send_bulk_sms 
from pavaman_backend.models import (CustomerRegisterDetails, PavamanAdminDetails, CategoryDetails,SubCategoryDetails,ProductsDetails,
                                    PaymentDetails,OrderProducts,FeedbackRating,CustomerAddress)
from openpyxl import Workbook
from io import BytesIO
from django.http import HttpResponse
import pytz

@csrf_exempt
def add_admin(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            username = data.get('username')
            email = data.get('email')
            mobile_no = data.get('mobile_no')
            password = data.get('password')
            status = data.get('status', 1)

            if not username or not email or not password:
                return JsonResponse({"error": "Username, email, and password are required.", "status_code": 400}, status=400)

            if PavamanAdminDetails.objects.filter(username=username).exists():
                return JsonResponse({"error": "Username already exists. Please choose a different username.", "status_code": 409}, status=409)

            if PavamanAdminDetails.objects.filter(email=email).exists():
                return JsonResponse({"error": "Email already exists. Please use a different email.", "status_code": 409}, status=409)

            admin = PavamanAdminDetails(username=username, email=email, password=password, status=int(status))
            admin.save()
            return JsonResponse({"message": "Admin added successfully", "id": admin.id, "status_code": 201}, status=201)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data in the request body.", "status_code": 400}, status=400)
        except IntegrityError:
            return JsonResponse({"error": "Database integrity error.", "status_code": 500}, status=500)
        except Exception as e:
            return JsonResponse({"error": f"An unexpected error occurred: {str(e)}", "status_code": 500}, status=500)

    return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)
# @csrf_exempt
# def admin_login(request):
#     if request.method == "POST":
#         try:
#             data = json.loads(request.body)
#             email = data.get('email', '').strip().lower()
#             password = data.get('password', '')

#             if not email or not password:
#                 return JsonResponse({"error": "Email and password are required.", "status_code": 400}, status=400)

#             admin = PavamanAdminDetails.objects.filter(email=email).first()

#             if not admin:
#                 return JsonResponse({"error": "Email not found.", "status_code": 404}, status=404)
#             if admin.password != password:
#                 return JsonResponse({"error": "Invalid email or password.", "status_code": 401}, status=401)

#             if admin.status != 1:
#                 return JsonResponse({"error": "Your account is inactive. Contact support.", "status_code": 403}, status=403)
#             request.session['admin_id'] = admin.id
#             request.session['admin_email'] = admin.email
#             request.session['admin_username'] = admin.username
#             request.session.modified = True

#             return JsonResponse({"message": "Login successful.", "username": admin.username, "email": admin.email, "id": admin.id, "status_code": 200}, status=200)

#         except json.JSONDecodeError:
#             return JsonResponse({"error": "Invalid JSON data in the request body.", "status_code": 400}, status=400)
#         except Exception as e:
#             return JsonResponse({"error": f"An unexpected error occurred: {str(e)}", "status_code": 500}, status=500)

#     return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)


#--------------------------
@csrf_exempt
def admin_login(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            email = data.get('email', '').strip().lower()
            password = data.get('password', '')

            if not email or not password:
                return JsonResponse({"error": "Email and password are required.", "status_code": 400}, status=400)

            admin = PavamanAdminDetails.objects.filter(email=email).first()

            if not admin:
                return JsonResponse({"error": "Email not found.", "status_code": 404}, status=404)
            if admin.password != password:
                return JsonResponse({"error": "Invalid email or password.", "status_code": 401}, status=401)

            if admin.status != 1:
                return JsonResponse({"error": "Your account is inactive. Contact support.", "status_code": 403}, status=403)
            otp = random.randint(100000, 999999)
            admin.otp = otp
            admin.save()
            
            success = send_otp_sms(admin.mobile_no, otp)
            if not success:
                return JsonResponse({"error": "Failed to send OTP. Try again later.", "status_code": 500}, status=500)
            return JsonResponse({
                "message": "OTP sent to your registered mobile number.",
                "status_code": 200,
                "email": admin.email  # Use this to verify in the next step
            }, status=200)
            # return JsonResponse({"message": "Login successful.", "username": admin.username, "email": admin.email, "id": admin.id, "status_code": 200}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data in the request body.", "status_code": 400}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"An unexpected error occurred: {str(e)}", "status_code": 500}, status=500)

    return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)

@csrf_exempt
def admin_verify_otp(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            email = data.get("email")
            otp = data.get("otp")

            if not email or not otp:
                return JsonResponse({"error": "Email and OTP are required.", "status_code": 400}, status=400)

            admin = PavamanAdminDetails.objects.filter(email=email).first()
            if not admin:
                return JsonResponse({"error": "Invalid email.", "status_code": 404}, status=404)
            if str(admin.otp) != str(otp):
                return JsonResponse({"error": "Invalid OTP.", "status_code": 401}, status=401)
            admin.otp = None
            admin.save()

            request.session['admin_id'] = admin.id
            request.session['admin_email'] = admin.email
            request.session['admin_username'] = admin.username
            request.session.modified = True

            # return JsonResponse({"message": "OTP verified. Login successful.", "status_code": 200}, status=200)
            return JsonResponse({"message": "OTP verified.Login successful.", "username": admin.username, "email": admin.email, "id": admin.id, "status_code": 200}, status=200)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data.", "status_code": 400}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"Unexpected error: {str(e)}", "status_code": 500}, status=500)

    return JsonResponse({"error": "Only POST method allowed.", "status_code": 405}, status=405)

def send_otp_sms(mobile_no, otp):
    message = f"Your OTP for admin login is: {otp}"
    try:
        send_bulk_sms([mobile_no], message)
        return True
    except Exception as e:
        print(f"Failed to send OTP to {mobile_no}: {e}")
        return False
#-------------------------------
@csrf_exempt
def admin_logout(request):
    if request.method == "POST":
        try:
            if 'admin_id' in request.session:
                request.session.flush()
                return JsonResponse({"message": "Logout successful.", "status_code": 200}, status=200)
            else:
                return JsonResponse({"error": "No active session found.", "status_code": 400}, status=400)

        except Exception as e:
            return JsonResponse({"error": f"An unexpected error occurred: {str(e)}", "status_code": 500}, status=500)

    return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)



# @csrf_exempt
# def add_category(request):
#     if request.method == 'POST':
#         try:
#             data = request.POST
#             category_name = data.get('category_name').lower()
#             admin_id = data.get('admin_id')
#             category_status = 1

#             if not admin_id:
#                 return JsonResponse({"error": "Admin is not logged in.", "status_code": 401}, status=401)

#             try:
#                 admin_data = PavamanAdminDetails.objects.get(id=admin_id)
#             except PavamanAdminDetails.DoesNotExist:
#                 return JsonResponse({"error": "Admin session expired or invalid.", "status_code": 401}, status=401)

#             if CategoryDetails.objects.filter(category_name=category_name).exists():
#                 return JsonResponse({"error": "Category name already exists.", "status_code": 409}, status=409)

#             if 'category_image' not in request.FILES:
#                 return JsonResponse({"error": "Category image file is required.", "status_code": 400}, status=400)

#             category_image = request.FILES['category_image']
#             allowed_extensions = ['png', 'jpg', 'jpeg']
#             file_extension = category_image.name.split('.')[-1].lower()
#             if file_extension not in allowed_extensions:
#                 return JsonResponse({"error": f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}", "status_code": 400}, status=400)

#             image_name = f"{category_name}_{category_image.name}"
#             image_name = image_name.replace('\\', '_')

#             image_path = os.path.join('static', 'images', 'category', image_name)
#             image_path = image_path.replace("\\", "/")

#             full_path = os.path.join(settings.BASE_DIR, image_path)
#             os.makedirs(os.path.dirname(full_path), exist_ok=True)

#             with open(full_path, 'wb') as f:
#                 for chunk in category_image.chunks():
#                     f.write(chunk)

#             current_time = datetime.utcnow() + timedelta(hours=5, minutes=30)
#             category = CategoryDetails(
#                 category_name=category_name, 
#                 admin=admin_data, 
#                 category_image=image_path,  # Store the path with forward slashes
#                 category_status=category_status,
#                 created_at=current_time
#             )
#             category.save()

#             return JsonResponse({
#                 "message": "Category added successfully",
#                 "category_id": category.id,
#                 "category_image_url": f"/{image_path}",
#                 "category_status": category.category_status,
#                 "status_code": 201
#             }, status=201)

#         except json.JSONDecodeError:
#             return JsonResponse({"error": "Invalid JSON data in the request body.", "status_code": 400}, status=400)
#         except Exception as e:
#             return JsonResponse({"error": f"An unexpected error occurred: {str(e)}", "status_code": 500}, status=500)

#     return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)

import boto3

@csrf_exempt
def add_category(request):
    if request.method == 'POST':
        try:
            data = request.POST
            category_name = data.get('category_name')
            admin_id = data.get('admin_id')
            category_status = 1

            if not admin_id:
                return JsonResponse({"error": "Admin is not logged in.", "status_code": 401}, status=401)

            try:
                admin_data = PavamanAdminDetails.objects.get(id=admin_id)
            except PavamanAdminDetails.DoesNotExist:
                return JsonResponse({"error": "Admin session expired or invalid.", "status_code": 401}, status=401)

            if CategoryDetails.objects.filter(category_name=category_name).exists():
                return JsonResponse({"error": "Category name already exists.", "status_code": 409}, status=409)

            if 'category_image' not in request.FILES:
                return JsonResponse({"error": "Category image file is required.", "status_code": 400}, status=400)
            category_image = request.FILES['category_image']
            allowed_extensions = ['png', 'jpg', 'jpeg']
            file_name, file_extension = os.path.splitext(category_image.name)
            file_extension = file_extension.lower().lstrip('.')  # Remove dot

            if file_extension not in allowed_extensions:
                return JsonResponse({
                    "error": f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}",
                    "status_code": 400
                }, status=400)

            # Clean category name and build S3 key
            safe_category_name = category_name.replace(' ', '_').replace('/', '_')
            safe_file_name = file_name.replace(' ', '_').replace('/', '_')
            s3_file_key = f"static/images/category/{safe_category_name}_{safe_file_name}.{file_extension}"

            # category_image = request.FILES['category_image']
            # allowed_extensions = ['png', 'jpg', 'jpeg']
            # file_extension = category_image.name.split('.')[-1].lower()
            # if file_extension not in allowed_extensions:
            #     return JsonResponse({
            #         "error": f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}",
            #         "status_code": 400
            #     }, status=400)

            # Upload image to S3
            s3 = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME
            )
            # Prepare the file path in the format "static/images/category/{category_name}.png"
            # category_name = category_name.replace(' ', '_').replace('/', '_')  # Replace spaces with underscores
            # s3_file_key = f"static/images/category/{category_name}_{category_image.name}"


            # s3_file_key = f"category_images/{category_name}_{category_image.name}"
            # s3_file_key = s3_file_key.replace("\\", "_")

            s3.upload_fileobj(
                category_image,
                settings.AWS_STORAGE_BUCKET_NAME,
                s3_file_key,
                ExtraArgs={'ContentType': category_image.content_type}
                # ExtraArgs={'ACL': 'public-read', 'ContentType': category_image.content_type}
            )

            image_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{s3_file_key}"

            current_time = datetime.utcnow() + timedelta(hours=5, minutes=30)
            category = CategoryDetails(
                category_name=category_name,
                admin=admin_data,
                category_image=s3_file_key,
                category_status=category_status,
                created_at=current_time
            )
            category.save()

            return JsonResponse({
                "message": "Category added successfully",
                "category_id": category.id,
                "category_image_url": image_url,
                "category_status": category.category_status,
                "status_code": 201
            }, status=201)

        except Exception as e:
            return JsonResponse({
                "error": f"An unexpected error occurred: {str(e)}",
                "status_code": 500
            }, status=500)

    return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)

# @csrf_exempt
# def view_categories(request):
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#             admin_id = data.get('admin_id')

#             if not admin_id:
#                 return JsonResponse({"error": "Admin Id is required.", "status_code": 400}, status=400)

#             admin_data = PavamanAdminDetails.objects.filter(id=admin_id).first()
#             if not admin_data:
#                 return JsonResponse({"error": "Admin not found or session expired.", "status_code": 401}, status=401)

#             categories = CategoryDetails.objects.filter(admin_id=admin_id,category_status=1)

#             if not categories.exists():
#                 return JsonResponse({"message": "No category details found", "status_code": 200}, status=200)


#             # category_list = [
#             #     {
#             #         "category_id": str(category.id),
#             #         "category_name": category.category_name,
#             #         "category_image_url": f"/static/images/category/{os.path.basename(category.category_image.replace('\\', '/'))}"
#             #     }
#             #     for category in categories
#             # ]
#             category_list = []
#             s3 = boto3.client(
#                 's3',
#                 aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
#                 aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
#                 region_name=settings.AWS_S3_REGION_NAME
#             )
#             for category in categories:
#                 # Construct the S3 URL dynamically
#                 s3_file_key = category.category_image.split('amazonaws.com/')[1]
#                 image_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{s3_file_key}"

#                 category_list.append({
#                     "category_id": str(category.id),
#                     "category_name": category.category_name,
#                     "category_image_url": image_url
#                 })


#             return JsonResponse(
#                 {"message": "Categories retrieved successfully.", "categories": category_list, "status_code": 200},
#                 status=200
#             )

#         except json.JSONDecodeError:
#             return JsonResponse({"error": "Invalid JSON data.", "status_code": 400}, status=400)
#         except Exception as e:
#             return JsonResponse({"error": f"An unexpected error occurred: {str(e)}", "status_code": 500}, status=500)

#     return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)

@csrf_exempt
def view_categories(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            admin_id = data.get('admin_id')

            if not admin_id:
                return JsonResponse({"error": "Admin Id is required.", "status_code": 400}, status=400)

            admin_data = PavamanAdminDetails.objects.filter(id=admin_id).first()
            if not admin_data:
                return JsonResponse({"error": "Admin not found or session expired.", "status_code": 401}, status=401)

            categories = CategoryDetails.objects.filter(admin_id=admin_id, category_status=1)

            if not categories.exists():
                return JsonResponse({"message": "No category details found", "status_code": 200}, status=200)

            category_list = []
            for category in categories:
                image_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{category.category_image}"
                category_list.append({
                    "category_id": str(category.id),
                    "category_name": category.category_name,
                    "category_image_url": image_url
                })


            return JsonResponse(
                {"message": "Categories retrieved successfully.", "categories": category_list, "status_code": 200},
                status=200
            )

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data.", "status_code": 400}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"An unexpected error occurred: {str(e)}", "status_code": 500}, status=500)

    return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)

@csrf_exempt
def edit_category(request):
    if request.method == 'POST':
        try:
            data = request.POST
            category_id = data.get('category_id')
            category_name = data.get('category_name').lower()
            admin_id = data.get('admin_id')

            if not admin_id:
                return JsonResponse({"error": "Admin is not logged in.", "status_code": 401}, status=401)
            if not category_id:
                return JsonResponse({"error": "Category ID is required.", "status_code": 400}, status=400)

            admin_data = PavamanAdminDetails.objects.filter(id=admin_id).first()
            if not admin_data:
                return JsonResponse({"error": "Admin not found or session expired.", "status_code": 401}, status=401)

            category = CategoryDetails.objects.filter(id=category_id, admin=admin_data, category_status=1).first()
            if not category:
                return JsonResponse({"error": "Category not found.", "status_code": 404}, status=404)

            # if CategoryDetails.objects.filter(category_name=category_name,id=category_id).exists():
            #     return JsonResponse({"error": "Category name already exists.", "status_code": 409}, status=409)
            if CategoryDetails.objects.filter(category_name=category_name).exclude(id=category_id).exists():
                return JsonResponse({"error": "Category name already exists.", "status_code": 409}, status=409)

            category.category_name = category_name

            if 'category_image' in request.FILES:
                category_image = request.FILES['category_image']

                allowed_extensions = ['png', 'jpg', 'jpeg']
                file_extension = category_image.name.split('.')[-1].lower()
                if file_extension not in allowed_extensions:
                    return JsonResponse({
                        "error": f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}",
                        "status_code": 400
                    }, status=400)

                formatted_category_name = category_name.replace(' ', '_').replace('/', '_')
                image_name = f"{formatted_category_name}_{category_image.name}"

                image_path = os.path.join('static', 'images', 'category', image_name)
                image_path_full = os.path.join(settings.BASE_DIR, image_path)

                os.makedirs(os.path.dirname(image_path_full), exist_ok=True)
                with open(image_path_full, 'wb') as f:
                    for chunk in category_image.chunks():
                        f.write(chunk)
                category.category_image = image_path.replace("\\", "/")

            category.save()

            return JsonResponse({
                "message": "Category updated successfully.",
                "category_id": str(category.id),
                "category_name": category.category_name,
                "category_image_url": f"/{category.category_image}",
                "status_code": 200
            }, status=200)

        except Exception as e:
            return JsonResponse({"error": f"An unexpected error occurred: {str(e)}", "status_code": 500}, status=500)

    return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)


# @csrf_exempt
# def edit_category(request):
#     if request.method == 'POST':
#         try:
#             data = request.POST
#             category_id = data.get('category_id')
#             category_name = data.get('category_name')
#             admin_id = data.get('admin_id')

#             if not admin_id:
#                 return JsonResponse({"error": "Admin is not logged in.", "status_code": 401}, status=401)
#             if not category_id:
#                 return JsonResponse({"error": "Category ID is required.", "status_code": 400}, status=400)

#             admin_data = PavamanAdminDetails.objects.filter(id=admin_id).first()
#             if not admin_data:
#                 return JsonResponse({"error": "Admin not found or session expired.", "status_code": 401}, status=401)

#             category = CategoryDetails.objects.filter(id=category_id, admin=admin_data, category_status=1).first()
#             if not category:
#                 return JsonResponse({"error": "Category not found.", "status_code": 404}, status=404)

#             if CategoryDetails.objects.filter(category_name__iexact=category_name).exclude(id=category_id).exists():
#                 return JsonResponse({"error": "Category name already exists.", "status_code": 409}, status=409)

#             category.category_name = category_name

#             # If a new category image is uploaded
#             if 'category_image' in request.FILES:
#                 category_image = request.FILES['category_image']
#                 allowed_extensions = ['png', 'jpg', 'jpeg']
#                 file_name, file_extension = os.path.splitext(category_image.name)
#                 file_extension = file_extension.lower().lstrip('.')  # remove leading dot

#                 if file_extension not in allowed_extensions:
#                     return JsonResponse({
#                         "error": f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}",
#                         "status_code": 400
#                     }, status=400)

#                 # Ensure category_name is correctly sanitized
#                 safe_category_name = category_name.replace(' ', '_').replace('/', '_')

#                 # Construct the final S3 file path with the category name and original image name
#                 modified_category_name = f"{safe_category_name}"
#                 safe_file_name = file_name.replace(' ', '_').replace('/', '_')

#                 # Construct the S3 file key (without '_mobile')
#                 s3_file_key = f"static/images/category/{modified_category_name}_{safe_file_name}.{file_extension}"

#                 # S3 client setup
#                 s3 = boto3.client(
#                     's3',
#                     aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
#                     aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
#                     region_name=settings.AWS_S3_REGION_NAME
#                 )

#                 # Delete the old image from S3 if it exists
#                 if category.category_image:
#                     try:
#                         s3.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=category.category_image)
#                     except Exception as delete_err:
#                         print("Warning: Could not delete old image from S3:", str(delete_err))

#                 # Upload the new image to S3 with the updated file name
#                 s3.upload_fileobj(
#                     category_image,
#                     settings.AWS_STORAGE_BUCKET_NAME,
#                     s3_file_key,
#                     ExtraArgs={'ContentType': category_image.content_type}
#                 )

#                 # Update the category image field in the database
#                 category.category_image = s3_file_key

#             else:
#                 # If no new image is uploaded, rename the existing image based on the updated category name

                         
#                 # If no new image is uploaded, rename the existing image based on the updated category name
#                 # Ensure category_name is correctly sanitized
#                 safe_category_name = category_name.replace(' ', '_').replace('/', '_')

#                 # Extract the file name and extension from the existing image path
#                 existing_file_name, file_extension = os.path.splitext(category.category_image)
#                 existing_file_name = existing_file_name.split('/')[-1]  # Get the image name without path

#                 # If the existing image has '_mobile' in the name, we should keep it
#                 if '_mobile' in existing_file_name:
#                     # Remove the existing category name and retain the '_mobile' suffix
#                     existing_image_name = existing_file_name.split('_')[-1]
#                     modified_category_name = f"{safe_category_name}_{existing_image_name}"
#                 else:
#                     # If no '_mobile' suffix, just use the new category name with the image name
#                     modified_category_name = f"{safe_category_name}_{existing_file_name}"

#                 # Construct the new S3 file path with the new category name and the original image name
#                 new_s3_file_key = f"static/images/category/{modified_category_name}{file_extension}"

#                 # S3 client setup
#                 s3 = boto3.client(
#                     's3',
#                     aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
#                     aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
#                     region_name=settings.AWS_S3_REGION_NAME
#                 )

#                 # Rename the file in S3
#                 try:
#                     # Copy the old file to the new location with the new name
#                     s3.copy_object(
#                         Bucket=settings.AWS_STORAGE_BUCKET_NAME,
#                         CopySource={
#                             'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
#                             'Key': category.category_image
#                         },
#                         Key=new_s3_file_key
#                     )

#                     # Delete the old image after copy
#                     s3.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=category.category_image)

#                     # Update the category image field in the database with the new file name
#                     category.category_image = new_s3_file_key
#                 except Exception as rename_err:
#                     print(f"Warning: Could not rename image on S3: {str(rename_err)}")


#             category.save()

#             # Construct the image URL
#             image_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{category.category_image}"

#             # Remove '_mobile' from the image URL (if present)
#             image_url_without_mobile = image_url.replace('_mobile', '')

#             return JsonResponse({
#                 "message": "Category updated successfully.",
#                 "category_id": category.id,
#                 "category_name": category.category_name,
#                 "category_image_url": image_url_without_mobile,  # Send the updated URL without '_mobile'
#                 "status_code": 200
#             }, status=200)

#         except Exception as e:
#             return JsonResponse({
#                 "error": f"An unexpected error occurred: {str(e)}",
#                 "status_code": 500
#             }, status=500)

#     return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)

@csrf_exempt
def delete_category(request):
    if request.method == 'POST':
        try:
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({"error": "Invalid JSON data.", "status_code": 400}, status=400)

            category_id = data.get('category_id')
            admin_id = data.get('admin_id')

            print(f"Admin ID: {admin_id}, Category ID: {category_id}")

            if not admin_id:
                return JsonResponse({"error": "Admin is not logged in.", "status_code": 401}, status=401)

            if not category_id:
                return JsonResponse({"error": "Category ID is required.", "status_code": 400}, status=400)

            admin_data = PavamanAdminDetails.objects.filter(id=admin_id).first()
            if not admin_data:
                return JsonResponse({"error": "Admin not found or session expired.", "status_code": 401}, status=401)

            category = CategoryDetails.objects.filter(id=category_id, admin=admin_data).first()
            if not category:
                return JsonResponse({"error": "Category not found or you do not have permission to delete this category.", "status_code": 404}, status=404)

            # if category.category_image:
            #     image_path = os.path.join(settings.BASE_DIR, category.category_image.replace('/', os.sep))
            #     if os.path.exists(image_path):
            #         os.remove(image_path)

            # If image exists, attempt to delete it from S3
            if category.category_image:
                s3 = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_S3_REGION_NAME
                )

                try:
                    s3.delete_object(
                        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                        Key=category.category_image
                    )
                except ClientError as e:
                    print(f"S3 deletion error: {e}")  # Log error, but continue with deletion
            category.delete()

            return JsonResponse({
                "message": "Category deleted successfully.",
                "status_code": 200
            }, status=200)

        except Exception as e:
            return JsonResponse({"error": f"An unexpected error occurred: {str(e)}", "status_code": 500}, status=500)

    return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)


# @csrf_exempt
# def add_subcategory(request):
#     if request.method == 'POST':
#         try:
#             data = request.POST
#             subcategory_name = data.get('subcategory_name').lower()
#             category_id = data.get('category_id')
#             admin_id = data.get('admin_id')
#             subcategory_status = 1

#             if not subcategory_name:
#                 return JsonResponse({"error": "Subcategory name is required.", "status_code": 400}, status=400)

#             if not admin_id:
#                 return JsonResponse({"error": "Admin is not logged in.", "status_code": 401}, status=401)

#             try:
#                 admin_data = PavamanAdminDetails.objects.get(id=admin_id)
#             except PavamanAdminDetails.DoesNotExist:
#                 return JsonResponse({"error": "Admin session expired or invalid.", "status_code": 401}, status=401)

#             try:
#                 category = CategoryDetails.objects.get(id=category_id, admin=admin_data)
#             except CategoryDetails.DoesNotExist:
#                 return JsonResponse({"error": "Category not found.", "status_code": 404}, status=404)

#             if SubCategoryDetails.objects.filter(sub_category_name=subcategory_name, category=category).exists():
#                 return JsonResponse({
#                     "error": f"Subcategory '{subcategory_name}' already exists under category '{category.category_name}'.",
#                     "status_code": 409
#                 }, status=409)

#             existing_subcategory = SubCategoryDetails.objects.filter(sub_category_name=subcategory_name).exclude(category=category).first()
#             if existing_subcategory:
#                 return JsonResponse({
#                     "error": f"Subcategory '{subcategory_name}' already exists under a different category '{existing_subcategory.category.category_name}'.",
#                     "status_code": 409
#                 }, status=409)

#             subcategory_image = request.FILES.get('sub_category_image', None)
#             if not subcategory_image:
#                 return JsonResponse({"error": "Subcategory image file is required.", "status_code": 400}, status=400)

#             llowed_extensions = ['png', 'jpg', 'jpeg']
#             file_name, file_extension = os.path.splitext(subcategory_image.name)
#             file_extension = file_extension.lower().lstrip('.')  # remove dot

#             if file_extension not in allowed_extensions:
#                 return JsonResponse({"error": f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}", "status_code": 400}, status=400)

#             # Safe file and path name
#             safe_subcat_name = subcategory_name.replace(' ', '_').replace('/', '_')
#             safe_file_name = file_name.replace(' ', '_').replace('/', '_')
#             s3_file_key = f"static/images/subcategory/{safe_subcat_name}_{safe_file_name}.{file_extension}"

#             # Upload image to AWS S3
#             s3 = boto3.client(
#                 's3',
#                 aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
#                 aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
#                 region_name=settings.AWS_S3_REGION_NAME
#             )
#             s3.upload_fileobj(
#                 subcategory_image,
#                 settings.AWS_STORAGE_BUCKET_NAME,
#                 s3_file_key,
#                 ExtraArgs={'ContentType': subcategory_image.content_type}
#             )

#             image_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{s3_file_key}"

#             # allowed_extensions = ['png', 'jpg', 'jpeg']
#             # file_extension = subcategory_image.name.split('.')[-1].lower()
#             # if file_extension not in allowed_extensions:
#             #     return JsonResponse({"error": f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}", "status_code": 400}, status=400)

#             # image_name = f"{subcategory_name}_{subcategory_image.name}".replace('\\', '_')
#             # image_path = os.path.join('static', 'images', 'subcategory', image_name).replace("\\", "/")

#             # full_path = os.path.join(settings.BASE_DIR, image_path)
#             # os.makedirs(os.path.dirname(full_path), exist_ok=True)

#             # with open(full_path, 'wb') as f:
#             #     for chunk in subcategory_image.chunks():
#             #         f.write(chunk)

#             current_time = datetime.utcnow() + timedelta(hours=5, minutes=30)

#             subcategory = SubCategoryDetails(
#                 sub_category_name=subcategory_name,
#                 category=category,
#                 sub_category_image=image_path,
#                 sub_category_status=subcategory_status,
#                 admin=admin_data,
#                 created_at=current_time
#             )
#             subcategory.save()

#             return JsonResponse({
#                 "message": "Subcategory added successfully",
#                 "subcategory_id": subcategory.id,
#                 "category_id": category.id,
#                 "category_name": category.category_name,
#                 "subcategory_image_url": image_url,
#                 # "subcategory_image_url": f"/{image_path}",
#                 "subcategory_status": subcategory.sub_category_status,
#                 "status_code": 201
#             }, status=201)

#         except Exception as e:
#             return JsonResponse({"error": f"An unexpected error occurred: {str(e)}", "status_code": 500}, status=500)

#     return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)


@csrf_exempt
def add_subcategory(request):
    if request.method == 'POST':
        try:
            data = request.POST

            sub_category_name = data.get('sub_category_name')  # Corrected key name
            category_id = data.get('category_id')
            admin_id = data.get('admin_id')
            sub_category_status = 1

            if not sub_category_name:
                return JsonResponse({"error": "Subcategory name is required.", "status_code": 400}, status=400)
            if not admin_id:
                return JsonResponse({"error": "Admin is not logged in.", "status_code": 401}, status=401)

            sub_category_name = sub_category_name.lower()

            try:
                admin_data = PavamanAdminDetails.objects.get(id=admin_id)
            except PavamanAdminDetails.DoesNotExist:
                return JsonResponse({"error": "Admin session expired or invalid.", "status_code": 401}, status=401)

            try:
                category = CategoryDetails.objects.get(id=category_id, admin=admin_data)
            except CategoryDetails.DoesNotExist:
                return JsonResponse({"error": "Category not found.", "status_code": 404}, status=404)

            if SubCategoryDetails.objects.filter(sub_category_name=sub_category_name, category=category).exists():
                return JsonResponse({
                    "error": f"Subcategory '{sub_category_name}' already exists under category '{category.category_name}'.",
                    "status_code": 409
                }, status=409)

            existing_subcategory = SubCategoryDetails.objects.filter(sub_category_name=sub_category_name).exclude(category=category).first()
            if existing_subcategory:
                return JsonResponse({
                    "error": f"Subcategory '{sub_category_name}' already exists under a different category '{existing_subcategory.category.category_name}'.",
                    "status_code": 409
                }, status=409)

            sub_category_image = request.FILES.get('sub_category_image', None)
            if not sub_category_image:
                return JsonResponse({"error": "Subcategory image file is required.", "status_code": 400}, status=400)

            allowed_extensions = ['png', 'jpg', 'jpeg']
            file_name, file_extension = os.path.splitext(sub_category_image.name)
            file_extension = file_extension.lower().lstrip('.')  # Remove the dot

            if file_extension not in allowed_extensions:
                return JsonResponse({
                    "error": f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}",
                    "status_code": 400
                }, status=400)

            # Prepare safe file name
            safe_subcat_name = sub_category_name.replace(' ', '_').replace('/', '_')
            safe_file_name = file_name.replace(' ', '_').replace('/', '_')
            s3_file_key = f"static/images/subcategory/{safe_subcat_name}_{safe_file_name}.{file_extension}"

            # Upload to S3
            s3 = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME
            )
            s3.upload_fileobj(
                sub_category_image,
                settings.AWS_STORAGE_BUCKET_NAME,
                s3_file_key,
                ExtraArgs={'ContentType': sub_category_image.content_type}
            )

            image_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{s3_file_key}"

            current_time = datetime.utcnow() + timedelta(hours=5, minutes=30)

            subcategory = SubCategoryDetails(
                sub_category_name=sub_category_name,
                category=category,
                sub_category_image=s3_file_key,  # store file path, not full URL
                sub_category_status=sub_category_status,
                admin=admin_data,
                created_at=current_time
            )
            subcategory.save()

            return JsonResponse({
                "message": "Subcategory added successfully",
                "subcategory_id": subcategory.id,
                "category_id": category.id,
                "category_name": category.category_name,
                "subcategory_image_url": image_url,
                "subcategory_status": subcategory.sub_category_status,
                "status_code": 201
            }, status=201)

        except Exception as e:
            return JsonResponse({"error": f"An unexpected error occurred: {str(e)}", "status_code": 500}, status=500)

    return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)



# @csrf_exempt
# def view_subcategories(request):
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body.decode('utf-8'))
#             admin_id = data.get('admin_id')
#             category_id = data.get('category_id')

#             if not admin_id or not category_id:
#                 return JsonResponse({
#                     "error": "Admin id and Category id are required.",
#                     "status_code": 400
#                 }, status=400)

#             try:
#                 admin = PavamanAdminDetails.objects.get(id=admin_id)
#                 category = CategoryDetails.objects.get(id=category_id, admin=admin)
#             except PavamanAdminDetails.DoesNotExist:
#                 return JsonResponse({"error": "Admin not found or session expired.", "status_code": 404}, status=404)
#             except CategoryDetails.DoesNotExist:
#                 return JsonResponse({"error": "Category not found.", "status_code": 404}, status=404)

#             subcategories = SubCategoryDetails.objects.filter(category=category).values(
#                 'id', 'sub_category_name', 'sub_category_image'
#             )

#             if not subcategories:
#                 return JsonResponse({
#                     "message": "No subcategories found.",
#                     "status_code": 200,
#                     "subcategories": []
#                 }, status=200)

#             return JsonResponse({
#                 "message": "Subcategories retrieved successfully.",
#                 "status_code": 200,
#                 "category_id": category.id,
#                 "category_name": category.category_name,
#                 "subcategories": list(subcategories)
#             }, status=200)

#         except json.JSONDecodeError:
#             return JsonResponse({
#                 "error": "Invalid JSON format.",
#                 "status_code": 400
#             }, status=400)
#         except Exception as e:
#             return JsonResponse({
#                 "error": f"An unexpected error occurred: {str(e)}",
#                 "status_code": 500
#             }, status=500)

#     return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)


@csrf_exempt
def view_subcategories(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            admin_id = data.get('admin_id')
            category_id = data.get('category_id')

            if not admin_id or not category_id:
                return JsonResponse({
                    "error": "Admin id and Category id are required.",
                    "status_code": 400
                }, status=400)

            try:
                admin = PavamanAdminDetails.objects.get(id=admin_id)
                category = CategoryDetails.objects.get(id=category_id, admin=admin)
            except PavamanAdminDetails.DoesNotExist:
                return JsonResponse({"error": "Admin not found or session expired.", "status_code": 404}, status=404)
            except CategoryDetails.DoesNotExist:
                return JsonResponse({"error": "Category not found.", "status_code": 404}, status=404)

            subcategories = SubCategoryDetails.objects.filter(category=category)

            subcategory_list = []
            for subcat in subcategories:
                if subcat.sub_category_image:
                    image_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{subcat.sub_category_image}"
                else:
                    image_url = None

                subcategory_list.append({
                    'id': subcat.id,
                    'sub_category_name': subcat.sub_category_name,
                    'sub_category_image': image_url,
                })

            if not subcategory_list:
                return JsonResponse({
                    "message": "No subcategories found.",
                    "status_code": 200,
                    "subcategories": []
                }, status=200)

            return JsonResponse({
                "message": "Subcategories retrieved successfully.",
                "status_code": 200,
                "category_id": category.id,
                "category_name": category.category_name,
                "subcategories": subcategory_list
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({
                "error": "Invalid JSON format.",
                "status_code": 400
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "error": f"An unexpected error occurred: {str(e)}",
                "status_code": 500
            }, status=500)

    return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)


# @csrf_exempt
# def edit_subcategory(request):
#     if request.method == 'POST':
#         try:
#             data = request.POST
#             subcategory_id = data.get('subcategory_id')
#             sub_category_name = data.get('subcategory_name').lower()
#             category_id = data.get('category_id')
#             admin_id = data.get('admin_id')

#             if not admin_id:
#                 return JsonResponse({"error": "Admin is not logged in.", "status_code": 401}, status=401)
#             if not subcategory_id:
#                 return JsonResponse({"error": "Subcategory ID is required.", "status_code": 400}, status=400)
#             if not sub_category_name:
#                 return JsonResponse({"error": "Subcategory Name is required.", "status_code": 400}, status=400)

#             admin_data = PavamanAdminDetails.objects.filter(id=admin_id).first()
#             if not admin_data:
#                 return JsonResponse({"error": "Admin not found or session expired.", "status_code": 401}, status=401)

#             category = CategoryDetails.objects.filter(id=category_id, admin=admin_data).first()
#             if not category:
#                 return JsonResponse({"error": "Category not found.", "status_code": 404}, status=404)

#             subcategory = SubCategoryDetails.objects.filter(id=subcategory_id, category=category).first()
#             if not subcategory:
#                 return JsonResponse({"error": "Subcategory not found.", "status_code": 404}, status=404)

#             existing_subcategory = SubCategoryDetails.objects.filter(
#                 sub_category_name=sub_category_name, category=category
#             ).exclude(id=subcategory_id).first()

#             if existing_subcategory:
#                 return JsonResponse({
#                     "error": f"Subcategory name already exists under {category.category_name}",
#                     "status_code": 409
#                 }, status=409)

#             subcategory.sub_category_name = sub_category_name

#             # Handle the image upload only if provided.
#             subcategory_image = request.FILES.get('sub_category_image', None)
#             if subcategory_image:
#                 allowed_extensions = ['png', 'jpg', 'jpeg']
#                 # Use the correct attribute to get the file name.
#                 file_extension = subcategory_image.name.split('.')[-1].lower()

#                 if file_extension not in allowed_extensions:
#                     return JsonResponse({"error": f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}", "status_code": 400}, status=400)

#                 # Generate a new image name using the sub_category_name and the original file name.
#                 image_name = f"{sub_category_name}_{subcategory_image.name}".replace('\\', '_')
#                 image_path = os.path.join('static', 'images', 'subcategory', image_name).replace("\\", "/")

#                 full_path = os.path.join(settings.BASE_DIR, image_path)
#                 os.makedirs(os.path.dirname(full_path), exist_ok=True)

#                 with open(full_path, 'wb') as f:
#                     for chunk in subcategory_image.chunks():
#                         f.write(chunk)

#                 subcategory.sub_category_image = image_path

#             subcategory.save()

#             return JsonResponse({
#                 "message": "Subcategory updated successfully.",
#                 "category_id": subcategory.category.id,
#                 "category_name": subcategory.category.category_name,
#                 "subcategory_id": subcategory.id,
#                 "subcategory_name": subcategory.sub_category_name,
#                 "subcategory_image_url": f"/static/{subcategory.sub_category_image}" if subcategory.sub_category_image else None,
#                 "status_code": 200
#             }, status=200)

#         except Exception as e:
#             return JsonResponse({"error": f"An unexpected error occurred: {str(e)}", "status_code": 500}, status=500)

#     return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)

@csrf_exempt
def edit_subcategory(request):
    if request.method == 'POST':
        try:
            data = request.POST
            subcategory_id = data.get('subcategory_id')
            sub_category_name = data.get('subcategory_name')
            category_id = data.get('category_id')
            admin_id = data.get('admin_id')

            if not admin_id:
                return JsonResponse({"error": "Admin is not logged in.", "status_code": 401}, status=401)
            if not subcategory_id:
                return JsonResponse({"error": "Subcategory ID is required.", "status_code": 400}, status=400)
            if not sub_category_name:
                return JsonResponse({"error": "Subcategory Name is required.", "status_code": 400}, status=400)

            admin_data = PavamanAdminDetails.objects.filter(id=admin_id).first()
            if not admin_data:
                return JsonResponse({"error": "Admin not found or session expired.", "status_code": 401}, status=401)

            category = CategoryDetails.objects.filter(id=category_id, admin=admin_data, category_status=1).first()
            if not category:
                return JsonResponse({"error": "Category not found.", "status_code": 404}, status=404)

            subcategory = SubCategoryDetails.objects.filter(id=subcategory_id, category=category).first()
            if not subcategory:
                return JsonResponse({"error": "Subcategory not found.", "status_code": 404}, status=404)

            if SubCategoryDetails.objects.filter(sub_category_name__iexact=sub_category_name, category=category).exclude(id=subcategory_id).exists():
                return JsonResponse({"error": "Subcategory name already exists under this category.", "status_code": 409}, status=409)

            subcategory.sub_category_name = sub_category_name.lower()

            if 'sub_category_image' in request.FILES:
                subcategory_image = request.FILES['sub_category_image']
                allowed_extensions = ['png', 'jpg', 'jpeg']
                file_name, file_extension = os.path.splitext(subcategory_image.name)
                file_extension = file_extension.lower().lstrip('.')

                if file_extension not in allowed_extensions:
                    return JsonResponse({
                        "error": f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}",
                        "status_code": 400
                    }, status=400)

                safe_subcategory_name = sub_category_name.replace(' ', '_').replace('/', '_')
                safe_file_name = file_name.replace(' ', '_').replace('/', '_')
                s3_file_key = f"static/images/subcategory/{safe_subcategory_name}_{safe_file_name}.{file_extension}"

                s3 = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_S3_REGION_NAME
                )

                # Delete old image from S3 if it exists
                if subcategory.sub_category_image:
                    try:
                        s3.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=subcategory.sub_category_image)
                    except Exception as delete_err:
                        print("Warning: Could not delete old subcategory image from S3:", str(delete_err))

                # Upload new image to S3
                s3.upload_fileobj(
                    subcategory_image,
                    settings.AWS_STORAGE_BUCKET_NAME,
                    s3_file_key,
                    ExtraArgs={'ContentType': subcategory_image.content_type}
                )

                subcategory.sub_category_image = s3_file_key

            subcategory.save()

            image_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{subcategory.sub_category_image}" if subcategory.sub_category_image else None

            return JsonResponse({
                "message": "Subcategory updated successfully.",
                "category_id": subcategory.category.id,
                "category_name": subcategory.category.category_name,
                "subcategory_id": subcategory.id,
                "subcategory_name": subcategory.sub_category_name,
                "subcategory_image_url": image_url,
                "status_code": 200
            }, status=200)

        except Exception as e:
            return JsonResponse({
                "error": f"An unexpected error occurred: {str(e)}",
                "status_code": 500
            }, status=500)

    return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)


@csrf_exempt
def delete_subcategory(request):
    if request.method == 'POST':
        try:
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({"error": "Invalid JSON data.", "status_code": 400}, status=400)

            subcategory_id = data.get('subcategory_id')
            category_id = data.get('category_id')
            admin_id = data.get('admin_id')

            print(f"Admin ID: {admin_id}, Category ID: {category_id}, Subcategory ID: {subcategory_id}")

            if not admin_id:
                return JsonResponse({"error": "Admin is not logged in.", "status_code": 401}, status=401)

            if not category_id:
                return JsonResponse({"error": "Category ID is required.", "status_code": 400}, status=400)

            if not subcategory_id:
                return JsonResponse({"error": "Subcategory ID is required.", "status_code": 400}, status=400)

            admin_data = PavamanAdminDetails.objects.filter(id=admin_id).first()
            if not admin_data:
                return JsonResponse({"error": "Admin not found or session expired.", "status_code": 401}, status=401)

            category = CategoryDetails.objects.filter(id=category_id, admin=admin_data).first()
            if not category:
                return JsonResponse({"error": "Category not found under this admin.", "status_code": 404}, status=404)

            subcategory = SubCategoryDetails.objects.filter(id=subcategory_id, category=category).first()
            if not subcategory:
                return JsonResponse({"error": "Subcategory not found.", "status_code": 404}, status=404)
            
             # If subcategory image exists, attempt to delete it from S3
            if subcategory.sub_category_image:
                s3 = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_S3_REGION_NAME
                )
                try:
                    s3.delete_object(
                        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                        Key=subcategory.sub_category_image
                    )
                except ClientError as e:
                    print(f"S3 deletion error: {e}")  # Log the error, but continue with deletion

            subcategory.delete()

            # if subcategory.sub_category_image:
            #     image_path = os.path.join(settings.BASE_DIR, 'static', subcategory.sub_category_image)
            #     if os.path.exists(image_path):
            #         os.remove(image_path)  # Delete image file from the server

            # subcategory.delete()

            return JsonResponse({
                "message": "Subcategory deleted successfully.",
                "status_code": 200
            }, status=200)

        except Exception as e:
            return JsonResponse({"error": f"An unexpected error occurred: {str(e)}", "status_code": 500}, status=500)

    return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)


@csrf_exempt
def add_product(request):
    if request.method == 'POST':
        try:
            if request.content_type == "application/json":
                try:
                    data = json.loads(request.body.decode('utf-8'))
                except json.JSONDecodeError:
                    return JsonResponse({"error": "Invalid JSON format.", "status_code": 400}, status=400)
            else:
                data = request.POST.dict()

            product_name = data.get('product_name').lower()
            sku_number = data.get('sku_number')
            price = data.get('price')
            quantity = data.get('quantity')
            discount = data.get('discount', 0.0)
            gst = data.get('gst', '0.0')
            description = data.get('description')
            admin_id = data.get('admin_id')
            category_id = data.get('category_id')
            sub_category_id = data.get('sub_category_id')

            if not all([product_name, sku_number, price, quantity, description, admin_id, category_id, sub_category_id]):
                return JsonResponse({"error": "Missing required fields.", "status_code": 400}, status=400)

            try:
                price = float(price)
                quantity = int(quantity)
                discount = float(discount)
                gst = float(gst)

                if discount > price:
                    return JsonResponse({"error": "Discount amount cannot be more than the price.", "status_code": 400}, status=400)
                
                # discount_percentage = (discount / price) * 100
                # discount = f"{round(discount_percentage)}%"

            except ValueError:
                return JsonResponse({"error": "Invalid format for price, quantity, or discount.", "status_code": 400}, status=400)

            availability = "Out of Stock" if quantity == 0 else "Very Few Products Left" if quantity <= 5 else "In Stock"

            try:
                admin = PavamanAdminDetails.objects.get(id=admin_id)
            except PavamanAdminDetails.DoesNotExist:
                return JsonResponse({"error": "Admin not found.", "status_code": 401}, status=401)

            try:
                category = CategoryDetails.objects.get(id=category_id, admin=admin)
            except CategoryDetails.DoesNotExist:
                return JsonResponse({"error": "Category not found", "status_code": 404}, status=404)

            try:
                sub_category = SubCategoryDetails.objects.get(id=sub_category_id, category=category)
            except SubCategoryDetails.DoesNotExist:
                return JsonResponse({"error": "Sub-category not found.", "status_code": 404}, status=404)

            if ProductsDetails.objects.filter(product_name=product_name).exists():
                return JsonResponse({"error": "Product name already exists.", "status_code": 409}, status=409)

            if ProductsDetails.objects.filter(sku_number=sku_number).exists():
                return JsonResponse({"error": "SKU number already exists.", "status_code": 409}, status=409)

            if 'product_images' not in request.FILES:
                return JsonResponse({"error": "Product images are required.", "status_code": 400}, status=400)

            image_files = request.FILES.getlist('product_images')
            if not image_files:
                return JsonResponse({"error": "At least one product image is required.", "status_code": 400}, status=400)

            # Initialize boto3 client for S3
            s3 = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME
            )

            product_images = []
            allowed_image_extensions = ['png', 'jpg', 'jpeg']
            for image in image_files:
                file_extension = image.name.split('.')[-1].lower()
                if file_extension not in allowed_image_extensions:
                    return JsonResponse({"error": f"Invalid image file type. Allowed types: {', '.join(allowed_image_extensions)}", "status_code": 400}, status=400)

                s3_key = f"static/images/products/{product_name.replace(' ', '_')}/{sku_number}_{image.name}"

                try:
                    s3.upload_fileobj(
                        image,
                        settings.AWS_STORAGE_BUCKET_NAME,
                        s3_key,
                        ExtraArgs={'ContentType': image.content_type}
                    )
                except ClientError as e:
                    return JsonResponse({"error": f"Failed to upload product image: {str(e)}", "status_code": 500}, status=500)

                product_images.append(s3_key)

            if 'material_file' not in request.FILES:
                return JsonResponse({"error": "Material file is required.", "status_code": 400}, status=400)

            material_file = request.FILES['material_file']
            allowed_material_extensions = ['pdf', 'doc']
            file_extension = material_file.name.split('.')[-1].lower()

            if file_extension not in allowed_material_extensions:
                return JsonResponse({"error": f"Invalid material file type. Allowed types: {', '.join(allowed_material_extensions)}", "status_code": 400}, status=400)

            material_key = f"static/materials/{product_name.replace(' ', '_')}.{file_extension}"

            try:
                s3.upload_fileobj(
                    material_file,
                    settings.AWS_STORAGE_BUCKET_NAME,
                    material_key,
                    ExtraArgs={'ContentType': material_file.content_type}
                )
            except ClientError as e:
                return JsonResponse({"error": f"Failed to upload material file: {str(e)}", "status_code": 500}, status=500)

            current_time = datetime.utcnow() + timedelta(hours=5, minutes=30)
            
            product = ProductsDetails(
                product_name=product_name,
                sku_number=sku_number,
                price=price,
                quantity=quantity,
                discount=discount,
                description=description,
                admin=admin,
                category=category,
                gst=gst,
                sub_category=sub_category,
                product_images=product_images,
                material_file=material_key,
                availability=availability,
                created_at=current_time,
                product_status=1,
                cart_status=False  # Setting cart_status to False
            )
            product.save()

            return JsonResponse({
                "message": "Product added successfully.",
                "category_id": str(product.category.id),
                "category_name": product.category.category_name,
                "subcategory_id": str(product.sub_category.id),
                "sub_category_name": product.sub_category.sub_category_name,
                "product_id": str(product.id),
                "availability": availability,
                "discount": f"{int(product.discount)}%" if isinstance(product.discount, (int, float)) else product.discount,
                "gst": f"{int(product.gst)}%" if isinstance(product.gst, (int, float)) else product.gst,
                "status_code": 201
            }, status=201)

        except Exception as e:
            return JsonResponse({"error": f"Unexpected error: {str(e)}", "status_code": 500}, status=500)

    return JsonResponse({"error": "Invalid request method. Only POST is allowed.", "status_code": 405}, status=405)








@csrf_exempt
def add_product_specifications(request):
    if request.method == 'POST':
        try:
            try:
                data = json.loads(request.body.decode('utf-8'))
            except json.JSONDecodeError:
                return JsonResponse({"error": "Invalid JSON format.", "status_code": 400}, status=400)

            admin_id = data.get('admin_id')
            category_id = data.get('category_id')
            sub_category_id = data.get('sub_category_id')
            product_id = data.get('product_id')
            new_specifications = data.get('specifications', [])  # List of dictionaries

            if not all([admin_id, category_id, sub_category_id, product_id]):
                return JsonResponse({"error": "Missing required fields.", "status_code": 400}, status=400)
            try:
                admin = PavamanAdminDetails.objects.get(id=admin_id)
            except PavamanAdminDetails.DoesNotExist:
                return JsonResponse({"error": "Admin not found.", "status_code": 401}, status=401)

            try:
                category = CategoryDetails.objects.get(id=category_id, admin=admin)
            except CategoryDetails.DoesNotExist:
                return JsonResponse({"error": "Category not found for this admin.", "status_code": 404}, status=404)

            try:
                sub_category = SubCategoryDetails.objects.get(id=sub_category_id, category=category)
            except SubCategoryDetails.DoesNotExist:
                return JsonResponse({"error": "Subcategory not found for this category.", "status_code": 404}, status=404)

            try:
                product = ProductsDetails.objects.get(id=product_id, category=category, sub_category=sub_category)
            except ProductsDetails.DoesNotExist:
                return JsonResponse({"error": "Product not found.", "status_code": 404}, status=404)
            if not isinstance(new_specifications, list):
                return JsonResponse({"error": "Specifications must be a list of objects.", "status_code": 400}, status=400)

            existing_specifications = product.specifications or {}

            for spec in new_specifications:
                if "name" in spec and "value" in spec:
                    spec_name = spec["name"]
                    
                    if spec_name in existing_specifications:
                        return JsonResponse({
                            "error": f"Specification '{spec_name}' already exists.",
                            "status_code": 400
                        }, status=400)
                    
                    existing_specifications[spec_name] = spec["value"]
                else:
                    return JsonResponse({"error": "Each specification must contain 'name' and 'value'.", "status_code": 400}, status=400)

            product.specifications = existing_specifications
            product.number_of_specifications = len(existing_specifications)  # Update count
            product.save()

            return JsonResponse({
                "message": "New specifications added successfully.",
                "product_id": str(product.id),
                "number_of_specifications": product.number_of_specifications,
                "specifications": product.specifications,
                "status_code": 200
            }, status=200)

        except Exception as e:
            return JsonResponse({"error": f"Unexpected error: {str(e)}", "status_code": 500}, status=500)

    return JsonResponse({"error": "Invalid request method. Only POST is allowed.", "status_code": 405}, status=405)

@csrf_exempt
def edit_product_specifications(request):
    if request.method == 'POST':
        try:
            try:
                data = json.loads(request.body.decode('utf-8'))
            except json.JSONDecodeError:
                return JsonResponse({"error": "Invalid JSON format.", "status_code": 400}, status=400)

            admin_id = data.get('admin_id')
            category_id = data.get('category_id')
            sub_category_id = data.get('sub_category_id')
            product_id = data.get('product_id')
            new_specifications = data.get('specifications', [])


            if not all([admin_id, category_id, sub_category_id, product_id]):
                return JsonResponse({"error": "Missing required fields.", "status_code": 400}, status=400)

            try:
                admin = PavamanAdminDetails.objects.get(id=admin_id)
            except PavamanAdminDetails.DoesNotExist:
                return JsonResponse({"error": "Admin not found.", "status_code": 401}, status=401)

            try:
                category = CategoryDetails.objects.get(id=category_id, admin=admin)
            except CategoryDetails.DoesNotExist:
                return JsonResponse({"error": "Category not found for this admin.", "status_code": 404}, status=404)

            try:
                sub_category = SubCategoryDetails.objects.get(id=sub_category_id, category=category)
            except SubCategoryDetails.DoesNotExist:
                return JsonResponse({"error": "Subcategory not found for this category.", "status_code": 404}, status=404)

            try:
                product = ProductsDetails.objects.get(id=product_id, category=category, sub_category=sub_category)
            except ProductsDetails.DoesNotExist:
                return JsonResponse({"error": "Product not found.", "status_code": 404}, status=404)

            if not isinstance(new_specifications, list):
                return JsonResponse({"error": "Specifications must be a list of objects.", "status_code": 400}, status=400)

            existing_specifications = product.specifications or {}

            for spec in new_specifications:
                if "name" in spec and "value" in spec:
                    existing_specifications[spec["name"]] = spec["value"]
                else:
                    return JsonResponse({"error": "Each specification must contain 'name' and 'value'.", "status_code": 400}, status=400)

            product.specifications = existing_specifications
            product.number_of_specifications = len(existing_specifications)  # Update count
            product.save()

            return JsonResponse({
                "message": "Specifications updated successfully.",
                "product_id": str(product.id),
                "number_of_specifications": product.number_of_specifications,
                "specifications": product.specifications,
                "status_code": 200
            }, status=200)

        except Exception as e:
            return JsonResponse({"error": f"Unexpected error: {str(e)}", "status_code": 500}, status=500)

    return JsonResponse({"error": "Invalid request method. Only POST is allowed.", "status_code": 405}, status=405)

@csrf_exempt
def view_products(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            admin_id = data.get('admin_id')
            category_id = data.get('category_id')
            sub_category_id = data.get('sub_category_id')

            if not admin_id or not category_id or not sub_category_id:
                return JsonResponse({
                    "error": "admin_id, category_id, and sub_category_id are required.",
                    "status_code": 400
                }, status=400)

            try:
                admin = PavamanAdminDetails.objects.get(id=admin_id)
                category = CategoryDetails.objects.get(id=category_id, admin=admin)
                sub_category = SubCategoryDetails.objects.get(id=sub_category_id, category=category)
            except PavamanAdminDetails.DoesNotExist:
                return JsonResponse({"error": "Admin not found.", "status_code": 404}, status=404)
            except CategoryDetails.DoesNotExist:
                return JsonResponse({"error": "Category not found.", "status_code": 404}, status=404)
            except SubCategoryDetails.DoesNotExist:
                return JsonResponse({"error": "Subcategory not found.", "status_code": 404}, status=404)

            products = ProductsDetails.objects.filter(
                admin=admin, category=category, sub_category=sub_category
            ).values(
                'id', 'product_name', 'sku_number', 'price', 'availability', 'quantity', 'cart_status','product_images','discount','gst','description'
            )

            product_list = []
            for product in products:
                image_url = None
                if product['product_images']:
                    image_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{product['product_images'][0]}"

                price = round(float(product['price']), 2)  # Round price to 2 decimals
                discount = round(float(product.get('discount') or 0), 2)  # Round discount to 2 decimals
                gst = round(float(product.get('gst') or 0), 2)  # Round GST to 2 decimals

                discount_amount = round(price * (discount / 100), 2)  # Round discount amount to 2 decimals
                final_price = round(price - discount_amount, 2)  # Round price after discount
                # gst_amount = round(price_after_discount * (gst / 100), 2)  # Round GST amount
                # final_price = round(price_after_discount + gst_amount, 2)  # Final price rounded to 2 decimals


                product_list.append({
                    "product_id": str(product['id']),
                    "product_name": product['product_name'],
                    "sku_number": product['sku_number'],
                    "price": f"{price:.2f}",
                    "availability": product['availability'],
                    "quantity": product['quantity'],
                    "cart_status":product['cart_status'],
                    "product_images": image_url,
                    "gst": f"{int(gst)}%",
                    "final_price": f"{final_price:.2f}",
                    # "product_images": product['product_images'][0] if product['product_images'] else None,
                    "product_discount": f"{int(discount)}%",
                    "product_description":product['description']
                })

            return JsonResponse({
                "message": "Products retrieved successfully.",
                "status_code": 200,
                "category_id": str(category.id),
                "category_name": category.category_name,
                "sub_category_id": str(sub_category.id),
                "sub_category_name": sub_category.sub_category_name,
                "products": product_list
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format.", "status_code": 400}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"An unexpected error occurred: {str(e)}", "status_code": 500}, status=500)

    return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)

@csrf_exempt
def view_product_details(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            admin_id = data.get('admin_id')
            category_id = data.get('category_id')
            sub_category_id = data.get('sub_category_id')
            product_id = data.get('product_id')

            if not all([admin_id, category_id, sub_category_id, product_id]):
                return JsonResponse({
                    "error": "admin_id, category_id, sub_category_id, and product_id are required.",
                    "status_code": 400
                }, status=400)
            try:
                admin = PavamanAdminDetails.objects.get(id=admin_id)
                category = CategoryDetails.objects.get(id=category_id, admin=admin)
                sub_category = SubCategoryDetails.objects.get(id=sub_category_id, category=category)
                product = ProductsDetails.objects.get(id=product_id, admin=admin, category=category, sub_category=sub_category)
            except PavamanAdminDetails.DoesNotExist:
                return JsonResponse({"error": "Admin not found.", "status_code": 404}, status=404)
            except CategoryDetails.DoesNotExist:
                return JsonResponse({"error": "Category not found.", "status_code": 404}, status=404)
            except SubCategoryDetails.DoesNotExist:
                return JsonResponse({"error": "Subcategory not found.", "status_code": 404}, status=404)
            except ProductsDetails.DoesNotExist:
                return JsonResponse({"error": "Product not found.", "status_code": 404}, status=404)

            image_urls = []
            if product.product_images:
                for image in product.product_images:
                    image_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{image}"
                    image_urls.append(image_url)

                    price = round(float(product.price), 2)
                    discount = round(float(product.discount or 0))
                    gst = round(float(product.gst or 0))


                    discount_amount = round(price * (discount / 100), 2)
                    final_price = round(price - discount_amount, 2)

            # GST calculation
                    # gst_amount = round(price_after_discount * (gst / 100), 2)
                    # final_price = round(price_after_discount + gst_amount, 2)


            product_data = {
                "product_id": str(product.id),
                "product_name": product.product_name,
                "sku_number": product.sku_number,
                "price": f"{price:.2f}",
                "discount": f"{discount}%",
                "discount_amount": f"{discount_amount:.2f}",
                "final_price": f"{final_price:.2f}",
                "gst": f"{gst}%",
                # "gst_amount": f"{gst_amount:.2f}",
                # "final_price": f"{final_price:.2f}",
                "availability": product.availability,
                "quantity": product.quantity,
                "description": product.description,
                # "product_images": product.product_images,
                # "material_file": product.material_file,
                "product_images": image_urls,  # All image URLs
                "material_file": f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{product.material_file}",
                "number_of_specifications": product.number_of_specifications,
                "specifications": product.specifications,
            }

            return JsonResponse({
                "message": "Product details retrieved successfully.",
                "status_code": 200,
                "category_id": str(category.id),
                "category_name": category.category_name,
                "sub_category_id": str(sub_category.id),
                "sub_category_name": sub_category.sub_category_name,
                "product_details": product_data
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format.", "status_code": 400}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"An unexpected error occurred: {str(e)}", "status_code": 500}, status=500)

    return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)



@csrf_exempt
def edit_product(request):
    if request.method == 'POST':
        try:
            # Check if request is JSON
            if request.content_type == "application/json":
                try:
                    data = json.loads(request.body.decode('utf-8'))
                except json.JSONDecodeError:
                    return JsonResponse({"error": "Invalid JSON format.", "status_code": 400}, status=400)
            else:
                data = request.POST.dict()

            # Extract required fields
            admin_id = data.get('admin_id')
            category_id = data.get('category_id')
            sub_category_id = data.get('sub_category_id')
            product_id = data.get('product_id')
            product_name = data.get('product_name').lower()
            sku_number = data.get('sku_number')
            price = data.get('price')
            quantity = data.get('quantity')
            discount = data.get('discount', 0.0)
            description = data.get('description')
            gst = float(data.get('gst', 0.0))

            # Ensure all required fields are present
            if not all([admin_id, category_id, sub_category_id, product_id, product_name, sku_number, price, quantity, description]):
                return JsonResponse({"error": "Missing required fields.", "status_code": 400}, status=400)

            # Convert price, quantity, and discount to proper types
            try:
                price = float(price)
                quantity = int(quantity)
                discount = float(discount)
            except ValueError:
                return JsonResponse({"error": "Invalid format for price, quantity, or discount.", "status_code": 400}, status=400)

            # Validate discount: it should not be greater than the price
            if discount > price:
                return JsonResponse({"error": "Discount cannot be greater than the price.", "status_code": 400}, status=400)

            # Determine product availability
            availability = "In Stock" if quantity > 10 else "Very Few Products Left" if quantity > 0 else "Out of Stock"

            # Validate admin
            try:
                admin = PavamanAdminDetails.objects.get(id=admin_id)
            except PavamanAdminDetails.DoesNotExist:
                return JsonResponse({"error": "Admin not found.", "status_code": 401}, status=401)

            # Validate category
            try:
                category = CategoryDetails.objects.get(id=category_id, admin=admin)
            except CategoryDetails.DoesNotExist:
                return JsonResponse({"error": "Category not found.", "status_code": 404}, status=404)

            # Validate sub-category
            try:
                sub_category = SubCategoryDetails.objects.get(id=sub_category_id, category=category)
            except SubCategoryDetails.DoesNotExist:
                return JsonResponse({"error": "Subcategory not found.", "status_code": 404}, status=404)

            # Validate product
            try:
                product = ProductsDetails.objects.get(id=product_id, category=category, sub_category=sub_category)
            except ProductsDetails.DoesNotExist:
                return JsonResponse({"error": "Product not found.", "status_code": 404}, status=404)

            # Ensure SKU number is unique
            if ProductsDetails.objects.exclude(id=product_id).filter(sku_number=sku_number).exists():
                return JsonResponse({"error": "SKU number already exists.", "status_code": 400}, status=400)

            # Ensure Product Name is unique
            if ProductsDetails.objects.exclude(id=product_id).filter(product_name=product_name).exists():
                return JsonResponse({"error": "Product name already exists.", "status_code": 400}, status=400)

            # Update product details
            old_product_name = product.product_name
            product.product_name = product_name
            product.sku_number = sku_number
            product.price = price
            product.quantity = quantity
            product.discount = discount
            product.description = description
            product.availability = availability
            product.cart_status = False  # Ensure cart_status is always False when updating

        
            product_images = []
            if 'product_images' in request.FILES:
                image_files = request.FILES.getlist('product_images')

                # If product name has changed, update the folder path
                if old_product_name != product_name:
                    old_product_folder = f"static/images/products/{old_product_name.replace(' ', '_').replace('/', '_')}"
                    new_product_folder = f"static/images/products/{product_name.replace(' ', '_').replace('/', '_')}"

                    # Initialize S3 client
                    s3 = boto3.client(
                        's3',
                        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                        region_name=settings.AWS_S3_REGION_NAME
                    )

                    # Delete old images from S3 (if they exist) and their folder
                    try:
                        response = s3.list_objects_v2(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Prefix=old_product_folder)
                        if 'Contents' in response:
                            objects_to_delete = [{'Key': obj['Key']} for obj in response['Contents']]
                            s3.delete_objects(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Delete={'Objects': objects_to_delete})
                    except Exception as delete_err:
                        print("Warning: Could not delete old product images from S3:", str(delete_err))

                else:
                    new_product_folder = f"static/images/products/{product_name.replace(' ', '_').replace('/', '_')}"

                # Upload new images to S3 with the new folder name (if product name changed)
                for image in image_files:
                    allowed_extensions = ['png', 'jpg', 'jpeg']
                    file_extension = image.name.split('.')[-1].lower()
                    if file_extension not in allowed_extensions:
                        return JsonResponse({"error": f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}", "status_code": 400}, status=400)

                    safe_image_name = f"{sku_number}_{image.name.replace(' ', '_').replace('/', '_')}"
                    s3_file_key = f"{new_product_folder}/{safe_image_name}"

                    try:
                        # Upload the image to S3, overwriting any existing files
                        s3.upload_fileobj(
                            image,
                            settings.AWS_STORAGE_BUCKET_NAME,
                            s3_file_key,
                            ExtraArgs={'ContentType': image.content_type}
                        )

                        product_images.append(s3_file_key)
                    except Exception as e:
                        return JsonResponse({"error": f"Failed to upload image to S3: {str(e)}", "status_code": 500}, status=500)

            product.product_images = product_images


            # Handle material file upload to S3
            if 'material_file' in request.FILES:
                material_file = request.FILES['material_file']
                allowed_extensions = ['pdf', 'doc']
                file_extension = material_file.name.split('.')[-1].lower()

                if file_extension not in allowed_extensions:
                    return JsonResponse({"error": f"Invalid material file type. Allowed types: {', '.join(allowed_extensions)}", "status_code": 400}, status=400)

                safe_material_name = f"{product_name}.{file_extension}"
                s3_material_key = f"static/materials/{safe_material_name}"

                try:
                    # Upload the material file to S3
                    s3.upload_fileobj(
                        material_file,
                        settings.AWS_STORAGE_BUCKET_NAME,
                        s3_material_key,
                        ExtraArgs={'ContentType': material_file.content_type}
                    )

                    product.material_file = s3_material_key
                except Exception as e:
                    return JsonResponse({"error": f"Failed to upload material file to S3: {str(e)}", "status_code": 500}, status=500)
            

            final_price = price - (price * discount / 100)
            # gst_amount = (discounted_price * gst) / 100
            # final_price = discounted_price + gst_amount
            # Save the updated product details
            product.save()

            return JsonResponse({
                "message": "Product updated successfully.",
                "category_id": str(product.category.id),
                "category_name": product.category.category_name,
                "subcategory_id": str(product.sub_category.id),
                "sub_category_name": product.sub_category.sub_category_name,
                "product_id": str(product.id),
                "availability": availability,
                "cart_status": product.cart_status,
                "price": round(price, 2),
                "discount": round(discount, 2),
                # "discounted_price": round(discounted_price, 2),
                "gst": round(gst, 2),
                # "gst_amount": round(gst_amount, 2),
                "final_price": round(final_price , 2),
                "status_code": 200
            }, status=200)

        except Exception as e:
            return JsonResponse({"error": f"Unexpected error: {str(e)}", "status_code": 500}, status=500)

    else:
        return JsonResponse({"error": "Invalid request method. Only POST is allowed.", "status_code": 405}, status=405)

@csrf_exempt
def delete_product(request):
    if request.method == 'POST':
        try:
            if request.content_type == "application/json":
                try:
                    data = json.loads(request.body.decode('utf-8'))
                except json.JSONDecodeError:
                    return JsonResponse({"error": "Invalid JSON format.", "status_code": 400}, status=400)
            else:
                data = request.POST.dict()

            admin_id = data.get('admin_id')
            category_id = data.get('category_id')
            sub_category_id = data.get('sub_category_id')
            product_id = data.get('product_id')

            if not all([admin_id, category_id, sub_category_id, product_id]):
                return JsonResponse({"error": "Missing required fields.", "status_code": 400}, status=400)

            try:
                admin = PavamanAdminDetails.objects.get(id=admin_id)
            except PavamanAdminDetails.DoesNotExist:
                return JsonResponse({"error": "Admin not found.", "status_code": 401}, status=401)

            try:
                category = CategoryDetails.objects.get(id=category_id, admin=admin)
            except CategoryDetails.DoesNotExist:
                return JsonResponse({"error": "Category not found.", "status_code": 404}, status=404)

            try:
                sub_category = SubCategoryDetails.objects.get(id=sub_category_id, category=category)
            except SubCategoryDetails.DoesNotExist:
                return JsonResponse({"error": "Sub-category not found.", "status_code": 404}, status=404)

            try:
                product = ProductsDetails.objects.get(id=product_id, category=category, sub_category=sub_category)
            except ProductsDetails.DoesNotExist:
                return JsonResponse({"error": "Product not found.", "status_code": 404}, status=404)

            # product_folder = f"static/images/products/{product.product_name.replace(' ', '_')}"
            # product_folder_path = os.path.join(settings.BASE_DIR, product_folder)
            # if os.path.exists(product_folder_path):
            #     shutil.rmtree(product_folder_path)

            # if product.material_file:
            #     material_file_path = os.path.join(settings.BASE_DIR, product.material_file).replace("\\", "/")

            #     if os.path.exists(material_file_path):
            #         try:
            #             os.remove(material_file_path)
            #         except Exception as e:
            #             return JsonResponse({"error":str(e), "status_code": 404}, status=404)
            #     else:
            #         return JsonResponse({"error":str(e), "status_code": 404}, status=404)
            # product.delete()
            # Delete product folder/files from S3 if exists
            s3 = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME
            )

            # Assume product_folder stores multiple images (if you uploaded them with folder structure in S3)
            product_folder_prefix = f"static/images/products/{product.product_name.replace(' ', '_')}/"

            try:
                # List all objects inside the folder and delete them
                response = s3.list_objects_v2(
                    Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                    Prefix=product_folder_prefix
                )
                if 'Contents' in response:
                    for item in response['Contents']:
                        s3.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=item['Key'])

            except ClientError as e:
                print(f"Error deleting product folder from S3: {e}")

            # Delete material file if uploaded separately
            if product.material_file:
                try:
                    s3.delete_object(
                        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                        Key=product.material_file
                    )
                except ClientError as e:
                    print(f"Error deleting material file from S3: {e}")

            # Finally delete the product record from database
            product.delete()

            return JsonResponse({
                "message": "Product and associated files deleted successfully.",
                "product_id": product_id,
                "status_code": 200
            }, status=200)

        except Exception as e:
            return JsonResponse({"error": f"Unexpected error: {str(e)}", "status_code": 500}, status=500)

    return JsonResponse({"error": "Invalid request method. Only POST is allowed.", "status_code": 405}, status=405)


@csrf_exempt
def search_categories(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            admin_id = data.get('admin_id')
            search_query = data.get('category_name', '').strip()  # Get search term

            if not admin_id:
                return JsonResponse({"error": "Admin Id is required.", "status_code": 400}, status=400)

            if not search_query:
                return JsonResponse({"error": "Atleast one character is required.", "status_code": 400}, status=400)

            admin_data = PavamanAdminDetails.objects.filter(id=admin_id).first()
            if not admin_data:
                return JsonResponse({"error": "Admin not found or session expired.", "status_code": 401}, status=401)

            categories = CategoryDetails.objects.filter(
                admin_id=admin_id,
                category_status=1,
                category_name__icontains=search_query
            )

            if not categories.exists():
                return JsonResponse({"message": "No category details found", "status_code": 200}, status=200)

            # category_list = [
            #     {
            #         "category_id": str(category.id),
            #         "category_name": category.category_name,
            #         "category_image_url": f"/static/images/category/{os.path.basename(category.category_image.replace('\\', '/'))}"
            #     }
            #     for category in categories
            # ]
            category_list = []
            for category in categories:
                image_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{category.category_image}"
                category_list.append({
                    "category_id": str(category.id),
                    "category_name": category.category_name,
                    "category_image_url": image_url
                })


            return JsonResponse(
                {"message": "Categories retrieved successfully.", "categories": category_list, "status_code": 200},
                status=200
            )

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data.", "status_code": 400}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"An unexpected error occurred: {str(e)}", "status_code": 500}, status=500)

    return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)



@csrf_exempt
def search_subcategories(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            admin_id = data.get('admin_id')
            category_id = data.get('category_id')
            sub_category_name = data.get('sub_category_name', '').strip()

            if not admin_id:
                return JsonResponse({"error": "Admin Id is required.", "status_code": 400}, status=400)

            if not category_id:
                return JsonResponse({"error": "Category Id is required.", "status_code": 400}, status=400)

            if sub_category_name == "": 
                return JsonResponse({"error": "Atleast one character is required.", "status_code": 400}, status=400)

            admin_data = PavamanAdminDetails.objects.filter(id=admin_id).first()
            if not admin_data:
                return JsonResponse({"error": "Admin not found or session expired.", "status_code": 401}, status=401)

            subcategories = SubCategoryDetails.objects.filter(
                admin_id=admin_id,
                category_id=category_id,
                sub_category_status=1,
                sub_category_name__icontains=sub_category_name  # Partial match
            )

            if not subcategories.exists():
                return JsonResponse({"message": "No subcategory details found", "status_code": 200}, status=200)

            # subcategory_list = [
            #     {
            #         "sub_category_id": str(subcategory.id),
            #         "sub_category_name": subcategory.sub_category_name,
            #         "sub_category_image": f"/static/images/subcategory/{os.path.basename(subcategory.sub_category_image.replace('\\', '/'))}",
            #         "category_id": str(subcategory.category_id)
            #     }
            #     for subcategory in subcategories
            # ]
            subcategory_list = []
            for subcategory in subcategories:
                image_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{subcategory.sub_category_image}"
                subcategory_list.append({
                    "sub_category_id": str(subcategory.id),
                    "sub_category_name": subcategory.sub_category_name,
                    "sub_category_image_url": image_url
                })

            return JsonResponse(
                {"message": "Subcategories retrieved successfully.", "subcategories": subcategory_list, "status_code": 200},
                status=200
            )

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data.", "status_code": 400}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"An unexpected error occurred: {str(e)}", "status_code": 500}, status=500)

    return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)


@csrf_exempt
def search_products(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            admin_id = data.get('admin_id')
            category_id = data.get('category_id')
            sub_category_id = data.get('sub_category_id')
            product_name = data.get('product_name', '').strip()  # Optional search term

            if not admin_id:
                return JsonResponse({"error": "Admin ID are required.", "status_code": 400}, status=400)
            if not category_id:
                return JsonResponse({"error": "Category ID are required.", "status_code": 400}, status=400)
            if not sub_category_id:
                return JsonResponse({"error": "Sub Category ID are required.", "status_code": 400}, status=400)

            if product_name == "":
                return JsonResponse({"error": "Atleast one character is required.", "status_code": 400}, status=400)

            admin_data = PavamanAdminDetails.objects.filter(id=admin_id).first()
            if not admin_data:
                return JsonResponse({"error": "Admin not found or session expired.", "status_code": 401}, status=401)

            products = ProductsDetails.objects.filter(
                admin_id=admin_id,
                category_id=category_id,
                sub_category_id=sub_category_id,
                product_status=1
            )

            if product_name:
                products = products.filter(product_name__icontains=product_name)

            if not products.exists():
                return JsonResponse({"message": "No product details found", "status_code": 200}, status=200)

            # product_list = []
            # for product in products:
            #     product_images = product.product_images
            #     if isinstance(product_images, list):
            #         product_image_url = (
            #             f"/static/images/products/{os.path.basename(product_images[0].replace('\\', '/'))}"
            #             if product_images else ""
            #         )
            #     elif isinstance(product_images, str):
            #         product_image_url = f"/static/images/products/{os.path.basename(product_images.replace('\\', '/'))}"
            #     else:
            #         product_image_url = ""

            #     product_list.append({
            #         "product_id": str(product.id),
            #         "product_name": product.product_name,
            #         "category_id": str(product.category_id),
            #         "sub_category_id": str(product.sub_category_id),
            #         "product_image_url": product_image_url,
            #     })
            product_list = []
            for product in products:
                product_images = product.product_images

                if isinstance(product_images, list) and product_images:
                    product_image_key = product_images[0]
                elif isinstance(product_images, str):
                    product_image_key = product_images
                else:
                    product_image_key = ""

                product_image_url = (
                    f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{product_image_key}"
                    if product_image_key else ""
                )
                product_list.append({
                    "product_id": str(product.id),
                    "product_name": product.product_name,
                    "category_id": str(product.category_id),
                    "sub_category_id": str(product.sub_category_id),
                    "product_image_url": product_image_url,
                })

            return JsonResponse(
                {"message": "Products retrieved successfully.", "products": product_list, "status_code": 200},
                status=200
            )

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data.", "status_code": 400}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"An unexpected error occurred: {str(e)}", "status_code": 500}, status=500)

    return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)


@csrf_exempt
def discount_products(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            admin_id = data.get('admin_id')

            if not admin_id:
                return JsonResponse({"error": "Admin ID is required.", "status_code": 400}, status=400)

            products = ProductsDetails.objects.filter(admin_id=admin_id, discount__gt=0)

            if not products.exists():
                return JsonResponse({
                    "message": "No products with discount found.",
                    "status_code": 200,
                    "admin_id": str(admin_id)
                }, status=200)

            # product_list = []
            # for product in products:
            #     product_images = product.product_images if isinstance(product.product_images, list) else []
            
            product_list = []
            for product in products:
                # Handle product images (can be list or string)
                if isinstance(product.product_images, list):
                    image_urls = [
                        f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{img}"
                        for img in product.product_images
                    ]
                elif isinstance(product.product_images, str):
                    image_urls = [
                        f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{product.product_images}"
                    ]
                else:
                    image_urls = []

                # Handle material file (if any)
                material_file_url = (
                    f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{product.material_file}"
                    if product.material_file else ""
                )

                price = float(product.price or 0)
                discount = float(product.discount or 0)
                gst = float(product.gst or 0)

                
                discounted_price = round(price - discount, 2)
                final_price = round((discount / price) * 100, 2) if price > 0 else 0
                # gst_amount = round((discounted_price * gst) / 100, 2)
                # final_price = round(discounted_price + gst_amount, 2)


                product_list.append({
                    "product_id": str(product.id),
                    "product_name": product.product_name,
                    "sku_number": product.sku_number,
                    "price": round(price, 2),
                    "gst": f"{round(gst, 2)}%",
                    "discount_amount": round(discounted_price, 2),
                    "discount": f"{round(discount, 2)}%",
                    "final_price":round(final_price, 2),
                    "quantity": product.quantity,
                    "material_file": material_file_url,
                    "description": product.description,
                    "number_of_specifications": product.number_of_specifications,
                    "specifications": product.specifications,
                    "product_images": image_urls,
                    "created_at": product.created_at,
                    "category": product.category.category_name if product.category else None,
                    "sub_category": product.sub_category.sub_category_name if product.sub_category else None,
                    "category_id": product.category_id,
                    "sub_category_id": product.sub_category_id,
                    "availability": product.availability,
                    "product_status": product.product_status,
                    "cart_status": product.cart_status,
                })

            return JsonResponse({
                "message": "Discount products retrieved successfully.",
                "products": product_list,
                "status_code": 200,
                "admin_id": str(admin_id)
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data.", "status_code": 400}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"An unexpected error occurred: {str(e)}", "status_code": 500}, status=500)

    return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)



# @csrf_exempt
# def download_discount_products_excel(request):
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#             admin_id = data.get('admin_id')

#             if not admin_id:
#                 return JsonResponse({"error": "Admin ID is required.", "status_code": 400}, status=400)

#             products = ProductsDetails.objects.filter(admin_id=admin_id)

#             if not products.exists():
#                 return JsonResponse({
#                     "message": "No products with discount found.",
#                     "status_code": 200,
#                     "admin_id": str(admin_id)
#                 }, status=200)

#             # Create Excel workbook
#             wb = Workbook()
#             ws = wb.active
#             ws.title = "Products Details"

#             # Define headers
#             headers = [
#                 "Product ID", "Product Name", "SKU Number", "Price", "Discount", "Final Price",
#                 "Quantity", "Material File", "Description", "Specifications Count", "Specifications",
#                 "Availability", "Product Status", "Cart Status",
#                 "Category", "Subcategory", "Category ID", "Subcategory ID", "Created At"
#             ]
#             ws.append(headers)

#             # Populate data
#             for product in products:
#                 final_price = float(product.price) - float(product.discount)
#                  # Generate the S3 URL for material file
#                 material_file_url = (
#                     f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{product.material_file}"
#                     if product.material_file else ""
#                 )

#                 ws.append([
#                     str(product.id),
#                     product.product_name,
#                     product.sku_number,
#                     float(product.price),
#                     float(product.discount),
#                     final_price,
#                     product.quantity,
#                     material_file_url,
#                     product.description,
#                     product.number_of_specifications,
#                     json.dumps(product.specifications) if isinstance(product.specifications, dict) else product.specifications,
#                     product.availability,
#                     product.product_status,
#                     product.cart_status,
#                     product.category.category_name if product.category else '',
#                     product.sub_category.sub_category_name if product.sub_category else '',
#                     product.category_id,
#                     product.sub_category_id,
#                     product.created_at.strftime('%Y-%m-%d %H:%M:%S') if product.created_at else ''
#                 ])

#             # Save to buffer
#             buffer = BytesIO()
#             wb.save(buffer)
#             buffer.seek(0)

#             # Return Excel as response
#             response = HttpResponse(
#                 buffer,
#                 content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
#             )
#             response['Content-Disposition'] = 'attachment; filename=Products_Details.xlsx'
#             return response

#         except json.JSONDecodeError:
#             return JsonResponse({"error": "Invalid JSON data.", "status_code": 400}, status=400)
#         except Exception as e:
#             return JsonResponse({"error": f"An unexpected error occurred: {str(e)}", "status_code": 500}, status=500)

#     return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)


@csrf_exempt
def download_discount_products_excel(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            admin_id = data.get('admin_id')

            if not admin_id:
                return JsonResponse({"error": "Admin ID is required.", "status_code": 400}, status=400)

            products = ProductsDetails.objects.filter(admin_id=admin_id)

            if not products.exists():
                return JsonResponse({
                    "message": "No products with discount found.",
                    "status_code": 200,
                    "admin_id": str(admin_id)
                }, status=200)

            # Create Excel workbook
            wb = Workbook()
            ws = wb.active
            ws.title = "Products Details"

            # Define headers
            headers = [
                "Product ID", "Product Name", "SKU Number", "Price", "Discount (%)", "GST (%)","GST Amount","Final Price",
                "Quantity", "Material File", "Description", "Specifications Count", "Specifications",
                "Availability", "Product Status", "Cart Status",
                "Category", "Subcategory", "Category ID", "Subcategory ID", "Created At"
            ]
            ws.append(headers)

            # Populate data
            for product in products:
                price = float(product.price)
                discount = float(product.discount)
                gst = float(product.gst) if hasattr(product, 'gst') and product.gst else 0
                final_price =  round((discount / price) * 100, 2) if price > 0 else 0
                # gst_amount = (final_price * gst / 100)
                # final_price = final_price + gst_amount  # Now includes GST

                 # Generate the S3 URL for material file
                material_file_url = (
                    f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{product.material_file}"
                    if product.material_file else ""
                )

                ws.append([
                    str(product.id),
                    product.product_name,
                    product.sku_number,
                    round(price, 2),
                    f"{round(discount)}%",
                    f"{round(gst)}%",
                    # round(gst_amount, 2),
                    round(final_price, 2),
                    product.quantity,
                    material_file_url,
                    product.description,
                    product.number_of_specifications,
                    json.dumps(product.specifications) if isinstance(product.specifications, dict) else product.specifications,
                    product.availability,
                    product.product_status,
                    product.cart_status,
                    product.category.category_name if product.category else '',
                    product.sub_category.sub_category_name if product.sub_category else '',
                    product.category_id,
                    product.sub_category_id,
                    product.created_at.strftime('%Y-%m-%d %H:%M:%S') if product.created_at else ''
                ])

            # Save to buffer
            buffer = BytesIO()
            wb.save(buffer)
            buffer.seek(0)

            # Return Excel as response
            response = HttpResponse(
                buffer,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

                # content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = 'attachment; filename=Products_Details.xlsx'

            # response['Content-Disposition'] = 'attachment; filename=Products_Details.xlsx'
            return response

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data.", "status_code": 400}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"An unexpected error occurred: {str(e)}", "status_code": 500}, status=500)

    return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)



@csrf_exempt
def apply_discount_by_subcategory_only(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            categories = data.get('categories')
            admin_id = data.get('admin_id')

            if not admin_id:
                return JsonResponse({"error": "admin_id is required.", "status_code": 400}, status=400)

            try:
                admin = PavamanAdminDetails.objects.get(id=admin_id, status=1)
            except PavamanAdminDetails.DoesNotExist:
                return JsonResponse({"error": "Admin not found or not active.", "status_code": 403}, status=403)

            if not categories or not isinstance(categories, list):
                return JsonResponse({"error": "categories must be a list.", "status_code": 400}, status=400)

            response_categories = []

            for cat_data in categories:
                category_id = cat_data.get('category_id')
                category_name = cat_data.get('category_name')
                sub_category_id = cat_data.get('sub_category_id')
                sub_category_name = cat_data.get('sub_category_name')
                discount_str = cat_data.get('discount')

                if not all([category_id, category_name, sub_category_id, sub_category_name, discount_str]):
                    return JsonResponse({
                        "error": "Each item must have category_id, category_name, sub_category_id, sub_category_name, and discount.",
                        "status_code": 400
                    }, status=400)

                if not discount_str.endswith('%'):
                    return JsonResponse({"error": "Invalid discount format. Must end with '%'.", "status_code": 400}, status=400)

                discount = float(discount_str.replace('%', ''))

                try:
                    category = CategoryDetails.objects.get(id=category_id, category_name=category_name)
                except CategoryDetails.DoesNotExist:
                    return JsonResponse({"error": f"Category '{category_name}' not found.", "status_code": 404}, status=404)

                try:
                    subcategory = SubCategoryDetails.objects.get(
                        id=sub_category_id,
                        sub_category_name=sub_category_name,
                        category_id=category_id
                    )
                except SubCategoryDetails.DoesNotExist:
                    return JsonResponse({
                        "error": f"Subcategory '{sub_category_name}' not found in category '{category_name}'.",
                        "status_code": 404
                    }, status=404)

                products = ProductsDetails.objects.filter(
                    category_id=category_id,
                    sub_category_id=sub_category_id,
                    product_status=1
                )

                updated_products = []

                for product in products:
                    price = float(product.price or 0)
                    discount = float(product.discount or 0)
                    gst = float(product.gst or 0)
                    discount_amount = (price * discount / 100) if price > 0 else 0
                    final_price = round(price - discount_amount, 2)


                    # Directly check and apply the GST value (if exists)
                    # gst = product.gst if product.gst else 0
                    # gst_amount = (final_price * gst / 100)
                    # final_price_with_gst = final_price + gst_amount
                    product.discount = discount
                    product.save(update_fields=['discount'])

                    updated_products.append({
                        "product_id": str(product.id),
                        "product_name": product.product_name,
                        "price": round(price, 2),
                        "discount": f"{round(discount, 2)}%",  # Added discount with '%' symbol
                        "gst": f"{round(gst, 2)}%",  # GST in percentage format
                        # "gst_amount": round(gst_amount, 2),  # GST amount calculated
                        "final_price": round(final_price, 2)
                    })

                response_categories.append({
                    "category_id": category_id,
                    "category_name": category_name,
                    "sub_category_id": sub_category_id,
                    "sub_category_name": sub_category_name,
                    "discount": f"{int(discount)}%",
                    "admin_id": admin_id,
                    "updated_products": updated_products
                })

            return JsonResponse({
                "categories": response_categories,
                "admin_id": admin_id,
                "status_code": 200
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format.", "status_code": 400}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"Server error: {str(e)}", "status_code": 500}, status=500)

    return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)

@csrf_exempt
def order_or_delivery_status(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed", "status_code": 405}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))

        admin_id = data.get("admin_id")
        customer_id =data.get("customer_id")
        product_order_id = data.get("product_order_id")
        action = data.get("action")  # either "dispatch" or "deliver"
        single_order_product_id = data.get("single_order_product_id")  # optional

        if not all([admin_id, product_order_id,customer_id, action]):
            return JsonResponse({"error": "Missing required fields", "status_code": 400}, status=400)

        payment = PaymentDetails.objects.filter(admin_id=admin_id, product_order_id=product_order_id,customer_id=customer_id).first()
        if not payment:
            return JsonResponse({"error": "Payment not found", "status_code": 404}, status=404)

        updated_orders = []

        # DISPATCH LOGIC
        if action == "Shipped":
            if single_order_product_id:
                if single_order_product_id not in payment.order_product_ids:
                    return JsonResponse({"error": "Invalid order product ID", "status_code": 404}, status=404)
                order = OrderProducts.objects.filter(id=single_order_product_id,customer_id=customer_id).first()
                if order:
                    order.shipping_status = "Shipped"
                    order.save()
                    updated_orders.append(order.id)
            else:
                for oid in payment.order_product_ids:
                    order = OrderProducts.objects.filter(id=oid,customer_id=customer_id).first()
                    if order:
                        order.shipping_status = "Shipped"
                        order.save()
                        updated_orders.append(order.id)
        elif action == "Delivered":
            if single_order_product_id:
                if single_order_product_id not in payment.order_product_ids:
                    return JsonResponse({"error": "Invalid order product ID", "status_code": 404}, status=404)
                order = OrderProducts.objects.filter(id=single_order_product_id, customer_id=customer_id).first()
                if order:
                    if order.shipping_status != "Shipped":
                        return JsonResponse({"error": "Cannot mark as Delivered before Shipped", "status_code": 400}, status=400)
                    order.delivery_status = "Delivered"
                    order.save()
                    updated_orders.append(order.id)
            else:
                for oid in payment.order_product_ids:
                    order = OrderProducts.objects.filter(id=oid, customer_id=customer_id).first()
                    if order:
                        if order.shipping_status != "Shipped":
                            return JsonResponse({
                                "error": f"OrderProduct ID {oid} has not been shipped yet",
                                "status_code": 400
                            }, status=400)
                        order.delivery_status = "Delivered"
                        order.save()
                        updated_orders.append(order.id)

        else:
            return JsonResponse({"error": "Invalid action type", "status_code": 400}, status=400)

        return JsonResponse({
            "message": f"{action.capitalize()} status updated successfully.",
            "updated_orders": updated_orders,
            "admin_id":str(admin_id),
            # "delivery_status": payment.Delivery_status,
            "status_code": 200
        })

    except Exception as e:
        return JsonResponse({"error": str(e), "status_code": 500}, status=500)
   
import pytz  

@csrf_exempt
def retrieve_feedback(request):
    if request.method == "POST":
        try:
           
            data = json.loads(request.body.decode("utf-8"))

            admin_id = data.get('admin_id')

            if not admin_id:
                return JsonResponse({
                    "error": "admin_id is required.",
                    "status_code": 400
                }, status=400)

         
            feedbacks = FeedbackRating.objects.filter(admin_id=admin_id)

            if not feedbacks.exists():
                return JsonResponse({"error": "No feedback found for this admin.", "status_code": 404}, status=404)
            feedback_data = []
            for feedback in feedbacks:
                try:
                    customer = CustomerRegisterDetails.objects.get(id=feedback.customer_id)
                    product = ProductsDetails.objects.get(id=feedback.product_id)
                    # Get first image from list (if available)
                    image_url = None
                    if product.product_images and isinstance(product.product_images, list):
                        first_image = product.product_images[0]
                        if first_image:
                            image_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{first_image}"

                    feedback_data.append({
                        "customer_id": customer.id,
                        "customer_name": f"{customer.first_name} {customer.last_name}",
                        "customer_email": customer.email,
                        "product_image":image_url,
                        "product_name":product.product_name,
                        "product_id": feedback.product.id,
                        "rating": feedback.rating,
                        "feedback": feedback.feedback,
                        "order_id": feedback.order_id,
                        "created_at": feedback.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    })
                except CustomerRegisterDetails.DoesNotExist:
                    # If customer not found, skip or handle as needed
                    continue
         
            feedbacks = FeedbackRating.objects.filter(admin_id=admin_id)

            if not feedbacks.exists():
                return JsonResponse({"error": "No feedback found for this admin.", "status_code": 404}, status=404)
            feedback_data = []
            for feedback in feedbacks:
                try:
                    customer = CustomerRegisterDetails.objects.get(id=feedback.customer_id)
                    product = ProductsDetails.objects.get(id=feedback.product_id)
                    # Get first image from list (if available)
                    image_url = None
                    if product.product_images and isinstance(product.product_images, list):
                        first_image = product.product_images[0]
                        if first_image:
                            image_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{first_image}"

                    feedback_data.append({
                        "customer_id": customer.id,
                        "customer_name": f"{customer.first_name} {customer.last_name}",
                        "customer_email": customer.email,
                        "product_image":image_url,
                        "product_name":product.product_name,
                        "product_id": feedback.product.id,
                        "rating": feedback.rating,
                        "feedback": feedback.feedback,
                        "order_id": feedback.order_id,
                        "created_at": feedback.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    })
                except CustomerRegisterDetails.DoesNotExist:
                    # If customer not found, skip or handle as needed
                    continue

            return JsonResponse({
                "feedback": feedback_data,
                "status_code": 200,
                "admin_id": str(admin_id)
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({
                "error": "Invalid JSON format.",
                "status_code": 400
            }, status=400)

        except Exception as e:
            return JsonResponse({
                "error": f"Server error: {str(e)}",
                "status_code": 500
            }, status=500)

    return JsonResponse({
        "error": "Invalid HTTP method. Only POST allowed.",
        "status_code": 405
    }, status=405)



@csrf_exempt
def report_inventory_summary(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
        admin_id = data.get('admin_id')

        if not admin_id:
            return JsonResponse({"error": "admin_id is required.", "status_code": 400}, status=400)

        total_products = ProductsDetails.objects.filter(admin_id=admin_id).count()
        total_customers = CustomerRegisterDetails.objects.filter(admin_id=admin_id).count()

        low_stock_products = ProductsDetails.objects.filter(
            admin_id=admin_id,
            quantity__lt=10
        ).values('product_name', 'sku_number', 'quantity')

        return JsonResponse({
            "total_products": total_products,
            "total_customers": total_customers,
            "low_stock_products": list(low_stock_products),
            "status_code": 200,
            "admin_id": admin_id
        }, status=200)
    
    except Exception as e:
        return JsonResponse({"error": str(e), "status_code": 500}, status=500)


from django.db.models import Sum
from django.db.models import Count

@csrf_exempt
def top_buyers_report(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)
    try:
        data = json.loads(request.body.decode("utf-8"))
        admin_id = data.get('admin_id')

        if not admin_id:
            return JsonResponse({"error": "admin_id is required.", "status_code": 400}, status=400)

        payments = PaymentDetails.objects.filter(admin_id=admin_id)

        all_order_product_ids = []
        for p in payments:
            if isinstance(p.order_product_ids, list):
                all_order_product_ids.extend(p.order_product_ids)

     
        buyers_data = (
            OrderProducts.objects
            .filter(admin_id=admin_id, id__in=all_order_product_ids)
            .values('customer_id')
            .annotate(
                product_count=Count('product_id'),      
                total_quantity=Sum('quantity')          
            )
            .order_by('-total_quantity')  
        )

        result = []
        for buyer in buyers_data:
            try:
                customer = CustomerRegisterDetails.objects.get(id=buyer['customer_id'])
                result.append({
                    "customer_id": customer.id,
                    "name": f"{customer.first_name} {customer.last_name}",
                    "email": customer.email,
                    "mobile_no": customer.mobile_no,
                    "product_count": buyer['product_count'],
                    "total_quantity": buyer['total_quantity']
                })
            except CustomerRegisterDetails.DoesNotExist:
                continue

        return JsonResponse({
            "buyers": result,
            "status_code": 200,
            "admin_id": admin_id
        }, status=200)

    except Exception as e:
        return JsonResponse({"error": str(e), "status_code": 500}, status=500)

from django.db.models import Count, F

@csrf_exempt
def customer_growth_by_state(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode('utf-8'))
            admin_id = data.get("admin_id")

            if not admin_id:
                return JsonResponse({
                    "status_code": 400,
                    "message": "admin_id is required."
                })

            # Filter customers for given admin_id with non-empty mobile number
            customers = CustomerRegisterDetails.objects.filter(
                admin_id=admin_id
            ).exclude(mobile_no="")

            # Filter matched addresses where mobile number is same as in CustomerRegisterDetails
            matched_addresses = CustomerAddress.objects.filter(
                customer__in=customers,
                mobile_number=F('customer__mobile_no')
            ).exclude(state="").values(
                'state',
                'district',
                'pincode',
                'mandal',
                'village',
                'postoffice'
            ).annotate(
                customer_count=Count('customer', distinct=True)
            ).order_by('-customer_count')

            return JsonResponse({
                "status_code": 200,
                "message": "Customer growth by state (mobile number match)",
                "data": list(matched_addresses)
            })

        except Exception as e:
            return JsonResponse({
                "status_code": 500,
                "message": "Error occurred.",
                "error": str(e)
            })
    else:
        return JsonResponse({
            "status_code": 405,
            "message": "Method Not Allowed. Use POST."
        }, status=405)




# from django.db.models.functions import TruncMonth
# @csrf_exempt
# def monthly_product_orders(request):
#     if request.method == "POST":
#         try:
#             data = json.loads(request.body.decode('utf-8'))
#             admin_id = data.get("admin_id")

#             if not admin_id:
#                 return JsonResponse({
#                     "status_code": 400,
#                     "message": "admin_id is required."
#                 })

#             # Monthly grouping of total products ordered by quantity
#             monthly_data = OrderProducts.objects.filter(
#                 admin_id=admin_id
#             ).annotate(
#                 month=TruncMonth('created_at')
#             ).values(
#                 'month'
#             ).annotate(
#                 total_quantity=Sum('quantity')
#             ).order_by('month')

#             # Format month as string
#             result = [
#                 {
#                     "month": item["month"].strftime("%Y-%m"),
#                     "total_quantity": item["total_quantity"]
#                 }
#                 for item in monthly_data
#             ]

#             return JsonResponse({
#                 "status_code": 200,
#                 "message": "Monthly total products ordered.",
#                 "data": result
#             })

#         except Exception as e:
#             return JsonResponse({
#                 "status_code": 500,
#                 "message": "Error occurred.",
#                 "error": str(e)
#             })
#     else:
#         return JsonResponse({
#             "status_code": 405,
#             "message": "Method Not Allowed. Use POST."
#         }, status=405)


from django.db.models.functions import TruncMonth
@csrf_exempt
def monthly_product_orders(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode('utf-8'))
            admin_id = data.get("admin_id")

            if not admin_id:
                return JsonResponse({
                    "status_code": 400,
                    "message": "admin_id is required."
                })

            # Get all successfully paid order IDs
            paid_order_ids = PaymentDetails.objects.filter(
                admin_id=admin_id,
                razorpay_payment_id__isnull=False
            ).values_list("order_product_ids", flat=True)

            # Flatten the list of JSONField lists
            order_ids = []
            for item in paid_order_ids:
                order_ids.extend(item)  # Because order_product_ids is a list (JSONField)

            # Monthly grouping of only paid orders
            monthly_data = OrderProducts.objects.filter(
                admin_id=admin_id,
                id__in=order_ids
            ).annotate(
                month=TruncMonth('created_at')
            ).values(
                'month'
            ).annotate(
                total_quantity=Sum('quantity')
            ).order_by('month')

            
            result = [
                {
                    "month": item["month"].strftime("%Y-%m"),
                    "total_quantity": item["total_quantity"]
                }
                for item in monthly_data
            ]

            return JsonResponse({
                "status_code": 200,
                "message": "Monthly total products ordered.",
                "data": result
            })

        except Exception as e:
            return JsonResponse({
                "status_code": 500,
                "message": "Error occurred.",
                "error": str(e)
            })
    else:
        return JsonResponse({
            "status_code": 405,
            "message": "Method Not Allowed. Use POST."
        }, status=405)
