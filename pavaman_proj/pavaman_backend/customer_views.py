from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError
from .models import (CustomerRegisterDetails, PavamanAdminDetails,CategoryDetails,ProductsDetails,
    SubCategoryDetails,CartProducts,CustomerAddress,OrderProducts,PaymentDetails,FeedbackRating)
import threading
import random
from django.utils import timezone
import json
import re
import uuid
from datetime import datetime, timedelta
# from django.shortcuts import get_object_or_404
from django.conf import settings
from django.core.mail import send_mail,EmailMessage
import requests
import os
from django.contrib.auth.hashers import make_password,check_password
from .sms_utils import send_bulk_sms  # Import SMS utility function
from django.db.models import Min, Max
from django.db.models import Sum
import razorpay
from datetime import datetime
import string
from django.http import FileResponse, JsonResponse
from decimal import Decimal

def is_valid_password(password):
    if len(password) < 8:
        return "Password must be at least 8 characters long."
    if not any(char.isdigit() for char in password):
        return "Password must contain at least one digit."
    if not any(char.isupper() for char in password):
        return "Password must contain at least one uppercase letter."
    if not any(char.islower() for char in password):
        return "Password must contain at least one lowercase letter."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return "Password must contain at least one special character."
    return None  # Valid password


def match_password(password, re_password):
    if password != re_password:
        return "Passwords must be same."
    return None  # If passwords match, return None

@csrf_exempt
def customer_register(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            first_name = data.get('first_name')
            last_name = data.get('last_name')
            email = data.get('email')
            mobile_no = data.get('mobile_no')
            password = data.get('password')
            re_password = data.get('re_password')
            status = 1
            register_status = 0
            verification_link = str(uuid.uuid4())
         
            if not all([first_name, last_name, email, mobile_no, password, re_password]):
                return JsonResponse(
                    {"error": "first_name,last_name, email, mobile_no and password are required.", "status_code": 400}, status=400
                )

            # Validate password format
            password_error = is_valid_password(password)
            if password_error:
                return JsonResponse({"error": password_error, "status_code": 400}, status=400)

            # Validate password match
            mismatch_error = match_password(password, re_password)
            if mismatch_error:
                return JsonResponse({"error": mismatch_error, "status_code": 400}, status=400)

             # Ensure email and mobile_no are unique
            existing_customer = CustomerRegisterDetails.objects.filter(email=email).first()
            if existing_customer:
                if existing_customer.password is None:  # Registered via Google
                    return JsonResponse({"error": "This email was registered using Google Sign-In. Please reset your password to proceed.", "status_code": 409}, status=409)
                return JsonResponse({"error": "Email already exists. Please use a different email.", "status_code": 409}, status=409)
            
            if CustomerRegisterDetails.objects.filter(mobile_no=mobile_no).exists():
                return JsonResponse({"error": "Mobile number already exists. Please use a different mobile number.", "status_code": 409}, status=409)

            admin = PavamanAdminDetails.objects.order_by('id').first()
            if not admin:
                return JsonResponse({"error": "No admin found in the system.", "status_code": 500}, status=500)

            # Convert time to IST timezone
            
            current_time = datetime.utcnow() + timedelta(hours=5, minutes=30)

            # Create & Save customer
            customer = CustomerRegisterDetails(
                first_name=first_name,
                last_name=last_name,
                email=email,
                mobile_no=mobile_no,
                password=make_password(password),  # Secure password hashing
                status=int(status),
                register_status=int(register_status),
                created_on=current_time,
                admin=admin,
                verification_link=verification_link,
                register_type="Mannual"
            )
            customer.save()

            # Update register_status to 1 after mobile number is stored
            customer.register_status = 1
            customer.save(update_fields=['register_status'])
            # Send the verification email
            send_verification_email(email,first_name,verification_link)

            return JsonResponse(
                {
                    "message": "Account Created Successfully. Verification link sent to email.",
                    "id": customer.id,
                    "status_code": 201,
                }, status=201
            )

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data.", "status_code": 400}, status=400)
        except IntegrityError:
            return JsonResponse({"error": "Database integrity error.", "status_code": 500}, status=500)
        except Exception as e:
            return JsonResponse({"error": f"An unexpected error occurred: {str(e)}", "status_code": 500}, status=500)

    return JsonResponse({"error": "Invalid HTTP method. Only POST allowed.", "status_code": 405}, status=405)

#verify_email for both
@csrf_exempt
def verify_email(request, verification_link):
    try:
        
        customer = CustomerRegisterDetails.objects.filter(verification_link=verification_link).first()

        if not customer:
            return JsonResponse({
                "error": "Invalid or expired verification link. Please request a new verification link.",
                "status_code": 400,
            }, status=400)
        
         # Check if the verification link not matches the latest one
        if customer.verification_link != verification_link:
            return JsonResponse({
                "error": "Verification link has expired. Please request a new verification link.",
                "status_code": 400,
            }, status=400)

       
        customer.account_status = 1  
        customer.verification_link = None
        customer.save(update_fields=["account_status","verification_link"])

        # if not verification_link
        return JsonResponse({
            "message": "Account successfully verified.",
            "status_code": 200,
        }, status=200)
    
    except CustomerRegisterDetails.DoesNotExist:
        return JsonResponse({
            "error": "Invalid verification link.",
            "status_code": 400,
        }, status=400)

# def send_verification_email(email, first_name, verification_link):
#     subject = "[Pavaman]Please Verify Your Account"
#     message = f"""
#     Hello {first_name},

#     Please click the link below to verify your account:

#     {settings.SITE_URL}/verify-email/{verification_link}/

#     If you didn't request this, you can safely ignore this email.

#     Thank You,  
#     Pavaman Team
#     """

#     send_mail(
#         subject,
#         message,
#         settings.DEFAULT_FROM_EMAIL,
#         [email],
#         fail_silently=False,
#     )

from django.core.mail import EmailMultiAlternatives
from email.mime.image import MIMEImage

def send_verification_email(email, first_name, verification_link):
    subject = "[Pavaman] Please Verify Your Email ✨"

    frontend_url = "http://localhost:3000"  # Change to production URL later
    full_link = f"{frontend_url}/verify-email/{verification_link}"

    text_content = f"""
    Hello {first_name},

    Please verify your email using this link: {full_link}
    """

    html_content = f"""
    <html>
    <head>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
            @media only screen and (max-width: 600px) {{
                .container {{
                    width: 90% !important;
                        padding: 20px !important;
                    }}
                .logo {{
                        max-width: 180px !important;
                        height: auto !important;
                }}

            }}
        </style>
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Inter', sans-serif; background-color: #f5f5f5;">
        <div class="container" style="margin: 40px auto; background-color: #ffffff; border-radius: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); padding: 40px 30px; text-align: center; max-width: 480px;">
            <img src="cid:logo_image" alt="Pavaman Logo" class="logo" style="max-width: 280px; height: auto; margin-bottom: 20px;" />
            
            <h2 style="margin-top: 0; color: #222;">Please verify your email </h2>
            <p style="color: #555; margin: 20px 0 30px;">
                To use Pavaman, click the verification button. This helps keep your account secure.
            </p>

            <a href="{full_link}" style="display: inline-block; padding: 14px 28px; background-color: #4450A2; color: #ffffff; font-weight: 600; border-radius: 8px; text-decoration: none; font-size: 16px;">
                Verify my account
            </a>

            <p style="color: #888; font-size: 14px; margin-top: 40px;">
                You're receiving this email because you have an account with Pavaman.<br/>
                If you're not sure why, just reply to this email.
            </p>
        </div>
    </body>
    </html>
    """

    email_message = EmailMultiAlternatives(
        subject, text_content, settings.DEFAULT_FROM_EMAIL, [email]
    )
    email_message.attach_alternative(html_content, "text/html")

    #Attach the local image
    logo_path = r"C:\Users\admin\Desktop\new_pav\pavaman_proj\static\images\aviation-logo.png"
    try:
        with open(logo_path, 'rb') as img_file:
            logo = MIMEImage(img_file.read())
            logo.add_header('Content-ID', '<logo_image>')
            logo.add_header('Content-Disposition', 'inline', filename="aviation-logo.png")
            email_message.attach(logo)
    except Exception as e:
        print(f"Failed to attach logo image: {e}")

    email_message.send()


@csrf_exempt
def customer_login(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            password = data.get('password')

            if not email or not password:
                return JsonResponse({"error": "Email and Password are required.", "status_code": 400}, status=400)

            try:
                customer = CustomerRegisterDetails.objects.get(email=email)
            except CustomerRegisterDetails.DoesNotExist:
                return JsonResponse({"error": "Invalid email or password.", "status_code": 401}, status=401)
            
            # Check if the customer registered via Google Sign-In
            if customer.password is None:
                return JsonResponse({"error": "You registered using Google Sign-In. Please reset your password.", "status_code": 401}, status=401)
            
            if customer.account_status != 1:
                return JsonResponse({"error": "Account is not activated. Please verify your email.", "status_code": 403}, status=403)

            if not check_password(password, customer.password):
                return JsonResponse({"error": "Invalid email or password.", "status_code": 401}, status=401)

            request.session['customer_id'] = customer.id
            request.session['email'] = customer.email
            request.session.set_expiry(3600)

            return JsonResponse(
                {"message": "Login successful.", 
                "customer_id": customer.id,
                "customer_name":customer.first_name + " " + customer.last_name,
                "customer_email":customer.email, 
                "status_code": 200}, status=200
            )

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data.", "status_code": 400}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"An unexpected error occurred: {str(e)}", "status_code": 500}, status=500)

    return JsonResponse({"error": "Invalid HTTP method. Only POST allowed.", "status_code": 405}, status=405)

#added session

@csrf_exempt
def google_login(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            token = data.get("token")

            if not token:
                return JsonResponse({"error": "Token is required"}, status=400)
            
            # Verify Google token
            google_url = f"https://oauth2.googleapis.com/tokeninfo?id_token={token}"
            response = requests.get(google_url)
            
            if response.status_code != 200:
                return JsonResponse({"error": "Failed to verify token"}, status=400)

            customer_info = response.json()

            if "error" in customer_info:
                return JsonResponse({"error": "Invalid Token"}, status=400)

            # Extract customer details
            email = customer_info.get("email")
            first_name = customer_info.get("given_name", "")
            last_name = customer_info.get("family_name", "")

            if not email:
                return JsonResponse({"error": "Email is required"}, status=400)

            # Check if customer exists
            customer = CustomerRegisterDetails.objects.filter(email=email).first()

            if customer:
                if customer.account_status == 1:  # Verified Account
                    #Set session here
                    request.session['customer_id'] = customer.id
                    request.session['email'] = customer.email
                    request.session.set_expiry(3600) 

                    return JsonResponse({
                        "message": "Login successful",
                        "existing_customer": True,
                        "customer_id": customer.id,
                        "email": customer.email,
                        "first_name": customer.first_name,
                        "last_name": customer.last_name,
                        "register_status": customer.register_status,
                    })
                else:
                    return JsonResponse({"error": "Account is not verified","email":customer.email}, status=403)
                   
            admin = PavamanAdminDetails.objects.order_by('id').first()
            if not admin:
                return JsonResponse({"error": "No admin found in the system.", "status_code": 500}, status=500)

            # If no existing customer, create a new Google account entry
            verification_link = str(uuid.uuid4())  # Generate verification link
            customer = CustomerRegisterDetails.objects.create(
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=None,  # Google login customers don't have a password
                verification_link=verification_link,
                register_type="Google",
                admin=admin,
            )

            # Send verification email
            send_verification_email(email,first_name,verification_link)

            return JsonResponse({
                "message": "Account Created Successfully. Verification email sent. Submit your mobile number after verification.",
                "new_customer": True,
                "customer_id": customer.id,
                "email": customer.email,
                "first_name": customer.first_name,
                "last_name": customer.last_name,
                "register_status": customer.register_status,
            })
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)

@csrf_exempt
def resend_verification_email(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            email = data.get("email")

            if not email:
                return JsonResponse({"error": "Email is required."}, status=400)

            # Check if the user exists
            customer = CustomerRegisterDetails.objects.filter(email=email).first()
            if not customer:
                return JsonResponse({"error": "User not found."}, status=404)

            if customer.account_status == 1:
                return JsonResponse({"error": "Account is already verified."}, status=400)

            # Generate a new verification link
            verification_link = str(uuid.uuid4())
            customer.verification_link = verification_link
            customer.save(update_fields=["verification_link"])

            # Fetch first_name from the database
            first_name = customer.first_name 
            # Send verification email
            send_verification_email(email,first_name,verification_link)

            return JsonResponse({
                "message": "Verification email resent successfully.",
                "email": email
            })

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)

@csrf_exempt
def google_submit_mobile(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            customer_id = data.get("customer_id")
            mobile_no = data.get("mobile_no")

            if not customer_id or not mobile_no:
                return JsonResponse({"error": "User ID and Mobile Number are required."}, status=400)
            if CustomerRegisterDetails.objects.filter(mobile_no=mobile_no).exists():
                return JsonResponse({"error": "Mobile number already exists. Please use a different mobile number.", "status_code": 409}, status=409)

            # Fetch user
            try:
                customer = CustomerRegisterDetails.objects.get(id=customer_id)
            except CustomerRegisterDetails.DoesNotExist:
                return JsonResponse({"error": "User not found."}, status=404)

            if customer.register_status == 1:
                return JsonResponse({"error": "Mobile number already submitted."}, status=400)

            # Generate verification link
            # verification_link = str(uuid.uuid4())
            customer.mobile_no = mobile_no
            customer.register_status = 1  # Mobile number is now added
            # customer.verification_link = verification_link
            customer.save(update_fields=["mobile_no", "register_status"])

            # # Send verification email
            # send_verification_email(customer.email, verification_link)

            return JsonResponse({
                "message": "Mobile number saved Sucessfully.",
                "customer_id": customer.id,
                "register_status": customer.register_status,
            })

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)


def generate_reset_token():
    # Generate a unique reset token.
    return str(uuid.uuid4())

def delete_otp_after_delay(customer_id):
    # Delete OTP and reset token after 2 minutes.
    try:
        customer = CustomerRegisterDetails.objects.filter(id=customer_id).first()
        if customer:
            customer.otp = None
            customer.reset_link = None
            # customer.changed_on = None
            customer.save()
            print(f"OTP for {customer_id} deleted after 2 minutes ")
    except Exception as e:
        print(f"Error deleting OTP: {e}")


# @csrf_exempt
# def otp_generate(request):
#     if request.method == "POST":
#         try:
#             data = json.loads(request.body)
#             identifier = data.get("identifier")

#             if not identifier:
#                 return JsonResponse({"error": "Email or Mobile number is required"}, status=400)

#             customer = None
#             otp_send_type = None

#             if "@" in identifier:
#                 customer = CustomerRegisterDetails.objects.filter(email=identifier).first()
#                 otp_send_type = "email"
#             else:
#                 # Just search the database using the number as it is (with country code)
#                 customer = CustomerRegisterDetails.objects.filter(mobile_no=identifier).first()
#                 otp_send_type = "mobile"

#             if not customer:
#                 return JsonResponse({"error": "User not found"}, status=404)
            
#             # **Check if account is verified (account_status=1)**
#             if customer.account_status != 1:
#                 return JsonResponse({"error": "Account is not verified. Please verify your email first."}, status=403)


#             # Generate OTP and Reset Token
#             otp = random.randint(100000, 999999)
#             reset_token = str(uuid.uuid4())

#             customer.otp = otp
#             customer.reset_link = reset_token
#             customer.otp_send_type = otp_send_type  # Store OTP send type
#             customer.changed_on = timezone.now()
#             customer.save()

#             # Start a background thread to delete OTP after 2 minutes
#             threading.Timer(120, delete_otp_after_delay, args=[customer.id]).start()

#             # Send OTP via email or SMS
#             if otp_send_type == "email":
#                 send_mail(
#                     "Your Password Reset OTP",
#                     f"Your OTP for password reset is: {otp}",
#                     settings.DEFAULT_FROM_EMAIL,
#                     [customer.email],
#                 )
#                 return JsonResponse({
#                     "message": "OTP sent to email",
#                     "otp":customer.otp,
#                     "reset_token":customer.reset_link

#                     })
#             else:
#                 send_bulk_sms([identifier], f"Your OTP for password reset is: {otp}. Do not share this with anyone.")
#                 return JsonResponse({
#                     "message": "OTP sent to mobile number",
#                     "otp":customer.otp,
#                     "reset_token":customer.reset_link
#                     })

#         except json.JSONDecodeError:
#             return JsonResponse({"error": "Invalid JSON data"}, status=400)

#     return JsonResponse({"error": "Invalid request method"}, status=405)


@csrf_exempt
def otp_generate(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            identifier = data.get("identifier")

            if not identifier:
                return JsonResponse({"error": "Email or Mobile number is required"}, status=400)

            customer = None
            otp_send_type = None

            if "@" in identifier:
                customer = CustomerRegisterDetails.objects.filter(email=identifier).first()
                otp_send_type = "email"
            else:
                # Just search the database using the number as it is (with country code)
                customer = CustomerRegisterDetails.objects.filter(mobile_no=identifier).first()
                otp_send_type = "mobile"

            if not customer:
                return JsonResponse({"error": "User not found"}, status=404)
            
            # **Check if account is verified (account_status=1)**
            if customer.account_status != 1:
                return JsonResponse({"error": "Account is not verified. Please verify your email first."}, status=403)


            # Generate OTP and Reset Token
            otp = random.randint(100000, 999999)
            reset_token = str(uuid.uuid4())

            customer.otp = otp
            customer.reset_link = reset_token
            customer.otp_send_type = otp_send_type  # Store OTP send type
            customer.changed_on = timezone.now()
            customer.save()

            # Start a background thread to delete OTP after 2 minutes
            threading.Timer(120, delete_otp_after_delay, args=[customer.id]).start()

            # Send OTP via email or SMS
            if otp_send_type == "email":
                send_password_reset_otp_email(customer)

                return JsonResponse({
                    "message": "OTP sent to email",
                    # "otp":customer.otp,
                    # "reset_token":customer.reset_link

                    })
            else:
                send_bulk_sms([identifier], f"Your OTP for password reset is: {otp}. Do not share this with anyone.")
                return JsonResponse({
                    "message": "OTP sent to mobile number",
                    # "otp":customer.otp,
                    # "reset_token":customer.reset_link
                    })

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)

from django.core.mail import EmailMultiAlternatives
from email.mime.image import MIMEImage

def send_password_reset_otp_email(customer):
    otp = customer.otp
    email = customer.email
    first_name = customer.first_name
    reset_token = customer.reset_link

     # Construct S3 image URL
    logo_url = f"{settings.AWS_S3_BUCKET_URL}/static/images/aviation-logo.png"


    subject = "[Pavaman] Your OTP for Password Reset 🔐"
    text_content = f"Hello {first_name},\n\nYour OTP for password reset is: {otp}"
    html_content = f"""
    <html>
    <head>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
            @media only screen and (max-width: 600px) {{
                .container {{
                    width: 90% !important;
                    padding: 20px !important;
                }}
                .logo {{
                    max-width: 180px !important;
                    height: auto !important;
                }}
                .otp {{
                    font-size: 24px !important;
                    padding: 10px 20px !important;
                }}
            }}
        </style>
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Inter', sans-serif; background-color: #f5f5f5;">
        <div class="container" style="margin: 40px auto; background-color: #ffffff; border-radius: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); padding: 40px 30px; text-align: center; max-width: 480px;">
            <img src="{logo_url}" alt="Pavaman Logo" class="logo" style="max-width: 280px; height: auto; margin-bottom: 20px;" />            <h2 style="margin-top: 0; color: #222;">Your OTP for Password Reset</h2>
            <p style="color: #555; margin-bottom: 30px;">
                Hello <strong>{first_name}</strong>, use the OTP below to reset your password. This OTP is valid for 2 minutes.
            </p>

            <p class="otp" style="font-size: 28px; font-weight: bold; color: #4450A2; background: #f2f2f2; display: inline-block; padding: 12px 24px; border-radius: 10px; letter-spacing: 4px;">
                {otp}
            </p>

            <p style="color: #888; font-size: 14px; margin-top: 20px;">
                If you didn't request this, you can safely ignore this email.<br/>
                You're receiving this because you have an account on Pavaman.
            </p>
        </div>
    </body>
    </html>
    """

    email_message = EmailMultiAlternatives(
        subject, text_content, settings.DEFAULT_FROM_EMAIL, [email]
    )
    email_message.attach_alternative(html_content, "text/html")

    # # Attach logo
    # logo_path = r"C:\Users\admin\Desktop\new_pav\pavaman_proj\static\images\aviation-logo.png"
    # try:
    #     with open(logo_path, 'rb') as img_file:
    #         logo = MIMEImage(img_file.read())
    #         logo.add_header('Content-ID', '<logo_image>')
    #         logo.add_header('Content-Disposition', 'inline', filename="aviation-logo.png")
    #         email_message.attach(logo)
    # except Exception as e:
    #     print(f"Failed to attach logo image: {e}")

    email_message.send()

@csrf_exempt
def verify_otp(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            identifier = data.get("identifier")  # Email or Mobile
            otp = data.get("otp")
            reset_link = data.get("reset_link")

            if not identifier or not otp or not reset_link:
                return JsonResponse({"error": "Email/Mobile, OTP, and Reset Link are required"}, status=400)

            # Check if user exists
            customer = CustomerRegisterDetails.objects.filter(
                email=identifier
            ).first() or CustomerRegisterDetails.objects.filter(
                mobile_no=identifier
            ).first()

            if not customer:
                return JsonResponse({"error": "User not found with the provided email or mobile number"}, status=404)

            # Check if reset link is valid
            if not customer.reset_link:
                return JsonResponse({"error": "Reset link has expired or is missing"}, status=400)

            if customer.reset_link != reset_link:
                return JsonResponse({"error": "Invalid reset link for this user"}, status=400)

            # Clear expired OTP for this customer
            customer.clear_expired_otp()

            # Check if OTP is valid
            if not customer.otp or str(customer.otp) != str(otp):
                return JsonResponse({"error": "Invalid OTP or OTP has expired"}, status=400)

            # OTP & Reset Link are valid, clear them
            customer.otp = None
            customer.reset_link = None
            customer.save()

            return JsonResponse({"message": "OTP verified successfully"})

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)


@csrf_exempt
def set_new_password(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            identifier = data.get("identifier")  # Email or Mobile
            new_password = data.get("new_password")
            confirm_password = data.get("confirm_password")

            if not identifier or not new_password or not confirm_password:
                return JsonResponse({"error": "Email/Mobile, New Password, and Confirm Password are required."}, status=400)

            # Find the user
            customer = CustomerRegisterDetails.objects.filter(
                email=identifier
            ).first() or CustomerRegisterDetails.objects.filter(
                mobile_no=identifier
            ).first()

            if not customer:
                return JsonResponse({"error": "User not found."}, status=404)

            # Validate password strength
            password_error = is_valid_password(new_password)
            if password_error:
                return JsonResponse({"error": password_error}, status=400)

            # Ensure new_password and confirm_password match
            match_error = match_password(new_password, confirm_password)
            if match_error:
                return JsonResponse({"error": match_error}, status=400)

            # Update the password securely
            customer.password = make_password(new_password)  # Hash the password before saving
            customer.save()

            return JsonResponse({"message": "Password updated successfully."})

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data."}, status=400)

    return JsonResponse({"error": "Invalid request method."}, status=405)


@csrf_exempt
def customer_logout(request):
    if request.method == 'POST':
        try:
            customer_id = request.session.get("customer_id")
            if customer_id:
                request.session.flush()  # Clears all session data
                return JsonResponse({
                    "message": "Logout successful.",
                    "status_code": 200
                }, status=200)
            else:
                return JsonResponse({
                    "error": "User not logged in.",
                    "status_code": 400
                }, status=400)

        except Exception as e:
            return JsonResponse({
                "error": f"An error occurred during logout: {str(e)}",
                "status_code": 500
            }, status=500)

    return JsonResponse({
        "error": "Invalid HTTP method. Only POST allowed.",
        "status_code": 405
    }, status=405)


@csrf_exempt
def view_categories_and_discounted_products(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            customer_id = data.get('customer_id')
            categories = CategoryDetails.objects.filter(category_status=1)
            category_list = [
                {
                    "category_id": str(category.id),
                    "category_name": category.category_name,
                    "category_image_url": f"{settings.AWS_S3_BUCKET_URL}/{category.category_image}"
                    # "category_image_url": f"/static/images/category/{os.path.basename(category.category_image.replace('\\', '/'))}"
                }
                for category in categories
            ] if categories.exists() else []

            products = ProductsDetails.objects.filter(discount__gt=0, product_status=1).select_related('category', 'sub_category')

            product_list = []
            for product in products:
                if isinstance(product.product_images, list) and product.product_images:
                     product_image_url = f"{settings.AWS_S3_BUCKET_URL}/{product.product_images[0]}"

                    # product_image_url = f"/static/images/products/{os.path.basename(product.product_images[0].replace('\\', '/'))}"
                else:
                    product_image_url = ""

                category_name = product.category.category_name if product.category else None
                sub_category_name = product.sub_category.sub_category_name if product.sub_category else None

                discounted_amount = (product.price * (product.discount or 0)) / 100
                final_price = (product.price - discounted_amount)

                gst = product.gst if product.gst else 0  # If no GST, assume 0
                # final_price += (final_price * gst) / 100

                product_list.append({
                    "product_id": str(product.id),
                    "product_name": product.product_name,
                    "product_image_url": product_image_url,
                    "price": product.price,
                    "gst": f"{gst}%",
                    "discount": f"{int(product.discount)}%" if product.discount else "0%",
                    "discounted_amount": round(discounted_amount, 2),
                    # "final_price": round(product.price - product.discount, 2),
                    "final_price": round(final_price, 2),
                    "category_id": str(product.category_id) if product.category_id else None,
                    "category_name": category_name,
                    "sub_category_id": str(product.sub_category_id) if product.sub_category_id else None,
                    "sub_category_name": sub_category_name,
                    "quantity":product.quantity,
                    "availability":product.availability
                })

            response_data = {
                "message": "Data retrieved successfully.",
                "categories": category_list,
                "discounted_products": product_list,
                "status_code": 200
            }

            if customer_id:
                response_data["customer_id"] = customer_id

            return JsonResponse(response_data, status=200)

        except Exception as e:
            return JsonResponse({"error": f"An unexpected error occurred: {str(e)}", "status_code": 500}, status=500)

    return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)


@csrf_exempt
def view_sub_categories_and_discounted_products(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            customer_id = data.get('customer_id')
            category_name = data.get('category_name')

            if not category_name:
                return JsonResponse({"error": "Category name is required.", "status_code": 400}, status=400)

            category = CategoryDetails.objects.filter(category_name__iexact=category_name, category_status=1).first()
            if not category:
                return JsonResponse({"error": "Category not found or inactive.", "status_code": 404}, status=404)

            if customer_id:
                customer_exists = CustomerRegisterDetails.objects.filter(id=customer_id, status=1).exists()
                if not customer_exists:
                    return JsonResponse({"error": "Customer not found.", "status_code": 401}, status=401)

            subcategories = SubCategoryDetails.objects.filter(category=category, sub_category_status=1)
            subcategory_list = [
                {
                    "sub_category_id": str(subcategory.id),
                    "sub_category_name": subcategory.sub_category_name,
                    "sub_category_image_url": f"{settings.AWS_S3_BUCKET_URL}/{subcategory.sub_category_image}"
                    # "sub_category_image_url": f"/static/images/subcategory/{os.path.basename(subcategory.sub_category_image.replace('\\', '/'))}" 
                    if subcategory.sub_category_image else ""
                }
                for subcategory in subcategories
            ]
            
        
            products = ProductsDetails.objects.filter(
                discount__gt=0,
                product_status=1
            )
            product_list = []
            for product in products:
                discounted_amount = (product.price * (product.discount or 0)) / 100
                final_price = round(product.price - discounted_amount)
                gst = product.gst if product.gst else 0  # If no GST, assume 0
                # final_price += (final_price * gst) / 100 

                product_image_url = ""
                if isinstance(product.product_images, list) and product.product_images:
                    product_image_url = f"{settings.AWS_S3_BUCKET_URL}/{product.product_images[0]}"
                product_list.append({
                        "product_id": str(product.id),
                        "product_name": product.product_name,
                        "product_image_url": product_image_url,
                        "price": round(product.price, 2), 
                        "gst": f"{gst}%", 
                        "discount": f"{int(product.discount)}%" if product.discount else "0%",
                        "final_price": round(final_price, 2),
                        "category_id": str(category.id),
                        "category_name": category.category_name,
                        "sub_category_id": str(product.sub_category.id),
                        "sub_category_name": product.sub_category.sub_category_name
                    })
           
            all_products = ProductsDetails.objects.filter(category=category, product_status=1)

            if not all_products.exists():
                return JsonResponse({"error": "No products found for the given category.", "status_code": 404}, status=404)

            all_prices = [
                round(product.price - (product.discount or 0), 2)
                for product in all_products
            ]
            min_price = min(all_prices)
            max_price = max(all_prices)

            if min_price == max_price:
                min_price = 0

            price_range = {
                "min_price": min_price,
                "max_price": max_price
            }

            response_data = {
                "message": "Data retrieved successfully.",
                "category_id": str(category.id),
                "category_name": category_name,
                "min_price": price_range["min_price"],
                "max_price": price_range["max_price"],
                "subcategories": subcategory_list,
                "discounted_products": product_list,
                "status_code": 200
            }

            if customer_id:
                response_data["customer_id"] = customer_id  

            return JsonResponse(response_data, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format.", "status_code": 400}, status=400)

        except Exception as e:
            return JsonResponse({"error": f"An unexpected error occurred: {str(e)}", "status_code": 500}, status=500)

    return JsonResponse({"error": "Invalid request method. Use POST.", "status_code": 405}, status=405)



@csrf_exempt
def view_products_by_category_and_subcategory(request, category_name, sub_category_name):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            customer_id = data.get('customer_id')

            try:
                category = CategoryDetails.objects.get(category_name=category_name)
                sub_category = SubCategoryDetails.objects.get(sub_category_name=sub_category_name, category=category)
                if customer_id:
                    customer = CustomerRegisterDetails.objects.get(id=customer_id)
            except CustomerRegisterDetails.DoesNotExist:
                return JsonResponse({"error": "Customer not found.", "status_code": 404}, status=404)
            except CategoryDetails.DoesNotExist:
                return JsonResponse({"error": "Category not found.", "status_code": 404}, status=404)
            except SubCategoryDetails.DoesNotExist:
                return JsonResponse({"error": "Subcategory not found.", "status_code": 404}, status=404)

            # Fetch products
            products = ProductsDetails.objects.filter(
                category=category, sub_category=sub_category, product_status=1
            ).values(
                'id', 'product_name', 'sku_number', 'price', 'availability', 'quantity', 'product_images', 'discount',  'gst','cart_status'
            )

            if not products.exists():
                return JsonResponse({"error": "No products found for the given sub category.", "status_code": 404}, status=404)
           
            # # Get min and max price
            # price_range = products.aggregate(
            #     product_min_price=Min("price"),
            #     product_max_price=Max("price")
            # )
            all_prices = [
                round(float(product['price']) - float(product.get('discount', 0)), 2)
                for product in products
            ]
            min_price = min(all_prices)
            max_price = max(all_prices)

            if min_price == max_price:
                min_price = 0

            price_range = {
                "product_min_price": min_price,
                "product_max_price": max_price
            }

            product_list = []
            for product in products:
                image_path = product['product_images'][0] if isinstance(product['product_images'], list) and product['product_images'] else None
                image_url = f"{settings.AWS_S3_BUCKET_URL}/{image_path}" if image_path else ""
                # image_url = product['product_images'][0] if isinstance(product['product_images'], list) and product['product_images'] else None
                # final_price = float(product['price']) - float(product.get('discount', 0))
                # discounted_amount = (product.price * (product.discount or 0)) / 100
                # final_price = round(product.price - discounted_amount)
                price = round(float(product['price']), 2)
                discount = float(product.get('discount') or 0)
                gst = float(product.get('gst') or 0)

                discounted_amount = (price * discount) / 100
                final_price = price - discounted_amount
                # final_price += (final_price * gst) / 100  # Add GST if available
                final_price = round(final_price, 2)

                product_list.append({
                    "product_id": str(product['id']),
                    "product_name": product['product_name'],
                    "sku_number": product['sku_number'],
                    "price": price,
                    "discount": f"{int(discount)}%",
                    "gst": f"{gst}%", 
                    "discounted_amount": round(discounted_amount, 2),
                    "final_price": final_price,
                    "availability": product['availability'],
                    "quantity": product['quantity'],
                    "product_image_url": image_url,
                    "cart_status": product['cart_status']
                    
                })

            response_data = {
                "message": "Products retrieved successfully.",
                "status_code": 200,
                "category_id":str(category.id),
                "category_name": category_name,
                "sub_category_id":str(sub_category.id),
                "sub_category_name": sub_category_name,
                "product_min_price": price_range["product_min_price"],
                "product_max_price": price_range["product_max_price"],
                "products": product_list
            }

            if customer_id:
                response_data["customer_id"] = str(customer_id)

            return JsonResponse(response_data, status=200)

        except Exception as e:
            return JsonResponse({"error": f"An unexpected error occurred: {str(e)}", "status_code": 500}, status=500)

    return JsonResponse({"error": "Invalid HTTP method. Use POST.", "status_code": 405}, status=405)




@csrf_exempt
def view_products_details(request, product_name):
    if request.method == 'POST':
        try:
            # Load data from request body
            data = json.loads(request.body)
            customer_id = data.get('customer_id')
            category_name = data.get('category_name')
            sub_category_name = data.get('sub_category_name')

            if not all([category_name, sub_category_name, product_name]):
                return JsonResponse({
                    "error": "category_name, sub_category_name, and product_name are required.",
                    "status_code": 400
                }, status=400)

            try:
                # Fetch category and subcategory
                category = CategoryDetails.objects.get(category_name=category_name)
                sub_category = SubCategoryDetails.objects.get(sub_category_name=sub_category_name, category=category)

                # Fetch product details
                product = ProductsDetails.objects.get(product_name=product_name, category=category, sub_category=sub_category)

                # Validate customer_id if provided
                if customer_id:
                    try:
                        customer = CustomerRegisterDetails.objects.get(id=customer_id)
                    except CustomerRegisterDetails.DoesNotExist:
                        return JsonResponse({"error": "Customer not found.", "status_code": 404}, status=404)

            except CategoryDetails.DoesNotExist:
                return JsonResponse({"error": "Category not found.", "status_code": 404}, status=404)
            except SubCategoryDetails.DoesNotExist:
                return JsonResponse({"error": "Subcategory not found.", "status_code": 404}, status=404)
            except ProductsDetails.DoesNotExist:
                return JsonResponse({"error": "Product not found.", "status_code": 404}, status=404)
            
            price = float(product.price)
            discount = float(product.discount or 0)
            gst = float(product.gst or 0)

            discounted_amount = round((price * discount) / 100, 2)
            final_price = price - discounted_amount
            # final_price += (final_price * gst) / 100
            final_price = round(final_price, 2)

            product_images = []
            if isinstance(product.product_images, list):
                for image_path in product.product_images:
                    if image_path:
                        product_images.append(f"{settings.AWS_S3_BUCKET_URL}/{image_path}")

            material_file_url = f"{settings.AWS_S3_BUCKET_URL}/{product.material_file}" if product.material_file else ""

            product_data = {
                "product_id": str(product.id),
                "product_name": product.product_name,
                "sku_number": product.sku_number,
                "price": round(price, 2),
                "gst": f"{int(gst)}%",
                "discount": f"{int(discount)}%",
                "discounted_amount": round(discounted_amount, 2),
                "final_price": final_price,  
                "availability": product.availability,
                "quantity": product.quantity,
                "description": product.description,
                "product_images":product_images,
                "material_file": material_file_url,
                "number_of_specifications": product.number_of_specifications,
                "specifications": product.specifications,
            }

            response_data = {
                "message": "Product details retrieved successfully.",
                "status_code": 200,
                "category_id": str(category.id),
                "category_name": category.category_name,
                "sub_category_id": str(sub_category.id),
                "sub_category_name": sub_category.sub_category_name,
                "product_details": product_data
            }

            if customer_id:
                response_data["customer_id"] = str(customer_id)

            return JsonResponse(response_data, status=200)

        except Exception as e:
            return JsonResponse({"error": f"An unexpected error occurred: {str(e)}", "status_code": 500}, status=500)

    return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)




@csrf_exempt
def add_product_to_cart(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            customer_id = data.get('customer_id')
            product_id = data.get('product_id')

            quantity = max(int(data.get('quantity', 1)), 1)
            if not customer_id or not product_id:
                return JsonResponse({
                    "error": "customer_id and product_id are required.",
                    "status_code": 400
                }, status=400)

            try:
                customer = CustomerRegisterDetails.objects.get(id=customer_id)
                product = ProductsDetails.objects.get(id=product_id)
                admin = PavamanAdminDetails.objects.order_by('id').first()
            
            except CustomerRegisterDetails.DoesNotExist:
                return JsonResponse({"error": "Customer not found.", "status_code": 404}, status=404)
            except ProductsDetails.DoesNotExist:
                return JsonResponse({"error": "Product not found.", "status_code": 404}, status=404)
            except PavamanAdminDetails.DoesNotExist:
                return JsonResponse({"error": "Admin not found.", "status_code": 404}, status=404)

            if not product.category or not product.sub_category:
                return JsonResponse({"error": "Product's category or subcategory is not set.", "status_code": 400}, status=400)

            if "in stock" not in product.availability.lower().strip() and "few" not in product.availability.lower().strip():
                return JsonResponse({
                    "error": "Product is out of stock.",
                    "status_code": 400
                }, status=400)
            if product.quantity < quantity:
                return JsonResponse({
                    "error": f"Only {product.quantity} quantity(s) of this product can be added or less.",
                    "status_code": 400
                }, status=400)


            # if product.quantity < quantity:
            #     return JsonResponse({
            #         "error": "Requested quantity is unavailable.",
            #         "status_code": 400
            #     }, status=400)

            current_time = datetime.utcnow() + timedelta(hours=5, minutes=30)
            cart_item, created = CartProducts.objects.get_or_create(
                customer=customer,
                product=product,
                admin=admin,
                category=product.category,
                sub_category=product.sub_category,
                defaults={"quantity": quantity, "added_at": current_time}
            )

            if not created:
                cart_item.quantity += quantity
                cart_item.save()

                 # Get price, discount, and gst
            price = float(product.price)
            discount = float(product.discount or 0)
            gst = float(product.gst or 0)

            # Calculate discounted amount and final price
            discounted_amount = round((price * discount) / 100, 2)
            final_price = price - discounted_amount

            # Apply GST to the final price
            # final_price += (final_price * gst) / 100
            final_price = round(final_price, 2)

            # Calculate total price based on quantity
            total_price = round(final_price * cart_item.quantity, 2)

            return JsonResponse({
                "message": "Product added to cart successfully.",
                "status_code": 200,
                "cart_id": cart_item.id,
                "product_id": product.id,
                "product_name": product.product_name,
                "quantity": cart_item.quantity,
                "price": round(price, 2),
                "discount": f"{discount}%",
                "gst": f"{gst}%",
                "final_price": final_price,
                "total_price": total_price,
                "cart_status": True,  # This should be determined dynamically
                "category_id": product.category.id,
                "category_name": product.category.category_name,
                "sub_category_id": product.sub_category.id,
                "sub_category_name": product.sub_category.sub_category_name
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format.", "status_code": 400}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"An unexpected error occurred: {str(e)}", "status_code": 500}, status=500)

    return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)


@csrf_exempt
def view_product_cart(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            customer_id = data.get('customer_id')
            # Fetch cart products for the given customer
            cart_items = CartProducts.objects.filter(customer_id=customer_id)

            if not cart_items.exists():
                return JsonResponse({"message": "Cart is empty.", "status_code": 200}, status=200)
            # product_ = ProductDetails.objects.filter(customer_id=customer_id)

            cart_data = []
            total_price = 0

            for item in cart_items:
                product = item.product
                price = round(float(product.price), 2)
                discount = round(float(product.discount or 0))
                gst = round(float(product.gst or 0))

                discounted_amount = round((price * discount) / 100, 2)
                final_price = round(price - discounted_amount, 2)

                # Apply GST to final price
                # final_price_with_gst = round(final_price + (final_price * gst) / 100, 2)

                # Calculate total price based on quantity
                item_total_price = round(final_price * item.quantity, 2)
                total_price += item_total_price
                
                image_path = product.product_images[0] if isinstance(product.product_images, list) and product.product_images else None
                image_url = f"{settings.AWS_S3_BUCKET_URL}/{image_path}" if image_path else ""

                cart_data.append({
                    "cart_id": item.id,
                    "product_id": product.id,
                    "product_name": product.product_name,
                    "quantity": item.quantity,
                    "price_per_item": price,
                    "discount": f"{discount}%" if discount else "0%",
                    "gst": f"{gst}%" if gst else "0%",
                    # "final_price_with_gst": final_price_with_gst,
                    "discounted_amount": discounted_amount,
                    "final_price": final_price,
                    "total_price": item_total_price,
                    "original_quantity":product.quantity,
                    "availability":product.availability,
                    "image":image_url,
                    "category": product.category.category_name if product.category else None,
                    "sub_category": product.sub_category.sub_category_name if product.sub_category else None
                })

            return JsonResponse({
                "message": "Cart retrieved successfully.",
                "status_code": 200,
                "customer_id": customer_id,
                "total_cart_value": total_price,
                "cart_items": cart_data
            }, status=200)

        except Exception as e:
            return JsonResponse({"error": f"An unexpected error occurred: {str(e)}", "status_code": 500}, status=500)

    return JsonResponse({"error": "Invalid HTTP method. Only GET is allowed.", "status_code": 405}, status=405)

@csrf_exempt
def delete_product_cart(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            customer_id = data.get("customer_id")
            product_id = data.get("product_id")  # Optional

            if not customer_id:
                return JsonResponse({"error": "customer_id is required.", "status_code": 400}, status=400)

            if product_id:
                deleted_count, _ = CartProducts.objects.filter(customer_id=customer_id, product_id=product_id).delete()
                
                if deleted_count == 0:
                    return JsonResponse({"error": "Product not found in cart.", "status_code": 404}, status=404)
                if not CartProducts.objects.filter(product_id=product_id).exists():
                    product = ProductsDetails.objects.get(id=product_id)
                    product.cart_status = False
                    product.save()

                return JsonResponse({
                    "message": f"Product {product_id} removed from cart.",
                    "status_code": 200
                }, status=200)
            else:
                cart_items = CartProducts.objects.filter(customer_id=customer_id)
                if not cart_items.exists():
                    return JsonResponse({"message": "Cart is already empty.", "status_code": 200}, status=200)

                product_ids = cart_items.values_list('product_id', flat=True)
                cart_items.delete()
                ProductsDetails.objects.filter(id__in=product_ids).update(cart_status=False)

                return JsonResponse({
                    "message": "All products removed from cart.",
                    "status_code": 200
                }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format.", "status_code": 400}, status=400)
        except ProductsDetails.DoesNotExist:
            return JsonResponse({"error": "Product not found.", "status_code": 404}, status=404)
        except Exception as e:
            return JsonResponse({"error": f"An unexpected error occurred: {str(e)}", "status_code": 500}, status=500)

    return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)



@csrf_exempt
def delete_selected_products_cart(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            customer_id = data.get("customer_id")
            product_ids = data.get("product_ids", [])

            if not customer_id or not product_ids:
                return JsonResponse({"error": "customer_id and product_ids are required.", "status_code": 400}, status=400)

            deleted_count, _ = CartProducts.objects.filter(customer_id=customer_id, product_id__in=product_ids).delete()

            if deleted_count == 0:
                return JsonResponse({"error": "Products not found in cart.", "status_code": 404}, status=404)

            ProductsDetails.objects.filter(id__in=product_ids).update(cart_status=False)

            return JsonResponse({
                "message": f"{deleted_count} product(s) removed from cart.",
                "status_code": 200
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format.", "status_code": 400}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"An unexpected error occurred: {str(e)}", "status_code": 500}, status=500)

    return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)

# API URLs
PINCODE_API_URL = "https://api.postalpincode.in/pincode/"
GEOLOCATION_API_URL = "https://nominatim.openstreetmap.org/search"



@csrf_exempt
def add_customer_address(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))

            # Extract required fields
            customer_id = data.get("customer_id")
            first_name = data.get("first_name")
            last_name = data.get("last_name")
            email = data.get("email")
            mobile_number = data.get("mobile_number")
            alternate_mobile = data.get("alternate_mobile", "")
            address_type = data.get("address_type", "home")
            pincode = data.get("pincode")
            street = data.get("street")
            landmark = data.get("landmark", "")

            if not all([customer_id, first_name, last_name, email, mobile_number, pincode, street]):
                return JsonResponse({"error": "All required fields must be provided.", "status_code": 400}, status=400)

            try:
                customer = CustomerRegisterDetails.objects.get(id=customer_id)
            except CustomerRegisterDetails.DoesNotExist:
                return JsonResponse({"error": "Customer does not exist.", "status_code": 400}, status=400)

            postoffice = mandal = village = district = state = country = ""
            latitude = longitude = None

            response = requests.get(f"{PINCODE_API_URL}{pincode}")
            if response.status_code == 200:
                pincode_data = response.json()
                if pincode_data and pincode_data[0].get("Status") == "Success":
                    post_office_data = pincode_data[0].get("PostOffice", [])[0] if pincode_data[0].get("PostOffice") else {}

                    postoffice = post_office_data.get("BranchType", "")
                    village = post_office_data.get("Name", "")
                    mandal = post_office_data.get("Block", "")
                    district = post_office_data.get("District", "")
                    state = post_office_data.get("State", "")
                    country = post_office_data.get("Country", "India")

            geo_params = {
                "q": f"{pincode},{district},{state},{country}",
                "format": "json",
                "limit": 1
            }

            geo_headers = {
                "User-Agent": "MyDjangoApp/1.0 saralkumar.kapilit@gmail.com"  # Replace with your email
            }

            geo_response = requests.get(GEOLOCATION_API_URL, params=geo_params, headers=geo_headers)

            if geo_response.status_code == 200:
                geo_data = geo_response.json()
                if geo_data:
                    latitude = geo_data[0].get("lat")
                    longitude = geo_data[0].get("lon")
                else:
                    return JsonResponse({"error": "Failed to fetch latitude and longitude for the provided address.", "status_code": 400}, status=400)
            else:
                return JsonResponse({"error": "Geolocation API request failed.", "status_code": geo_response.status_code}, status=geo_response.status_code)

            customer_address = CustomerAddress.objects.create(
                customer=customer,
                first_name=first_name,
                last_name=last_name,
                email=email,
                mobile_number=mobile_number,
                alternate_mobile=alternate_mobile,
                address_type=address_type,
                pincode=pincode,
                street=street,
                landmark=landmark,
                village=village,
                mandal=mandal,
                postoffice=postoffice,
                district=district,
                state=state,
                country=country,
                latitude=latitude,
                longitude=longitude
            )

            return JsonResponse({
                "message": "Customer address added successfully.",
                "status_code": 200,
                "address_id": customer_address.id,
                "pincode_details": {
                    "postoffice": postoffice,
                    "village": village,
                    "mandal": mandal,
                    "district": district,
                    "state": state,
                    "country": country,
                    "landmark": landmark,
                    "latitude": latitude,
                    "longitude": longitude
                }
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format.", "status_code": 400}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"An unexpected error occurred: {str(e)}", "status_code": 500}, status=500)

    return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)


@csrf_exempt
def view_customer_address(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            customer_id = data.get("customer_id")

            if not customer_id:
                return JsonResponse({"error": "Customer ID is required.", "status_code": 400}, status=400)
            addresses = CustomerAddress.objects.filter(customer_id=customer_id)

            if not addresses.exists():
                return JsonResponse({"error": "No address found for the given customer ID.", "status_code": 404}, status=404)

            address_list = []
            for address in addresses:
                address_list.append({
                    "address_id": address.id,
                    "first_name": address.first_name,
                    "last_name": address.last_name,
                    "email": address.email,
                    "mobile_number": address.mobile_number,
                    "alternate_mobile": address.alternate_mobile,
                    "address_type": address.address_type,
                    "pincode": address.pincode,
                    "street": address.street,
                    "landmark": address.landmark,
                    "village": address.village,
                    "mandal": address.mandal,
                    "postoffice": address.postoffice,
                    "district": address.district,
                    "state": address.state,
                    "country": address.country,
                    "latitude": address.latitude,
                    "longitude": address.longitude
                })

            return JsonResponse({
                "message": "Customer addresses retrieved successfully.",
                "status_code": 200,
                "addresses": address_list
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format.", "status_code": 400}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"An unexpected error occurred: {str(e)}", "status_code": 500}, status=500)

    return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)


GEOLOCATION_API_URL = "https://nominatim.openstreetmap.org/search"

@csrf_exempt
def edit_customer_address(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            address_id = data.get("address_id")
            customer_id = data.get("customer_id")
            first_name = data.get("first_name")
            last_name = data.get("last_name")
            email = data.get("email")
            mobile_number = data.get("mobile_number")
            alternate_mobile = data.get("alternate_mobile", "")
            address_type = data.get("address_type", "home")
            pincode = data.get("pincode")
            street = data.get("street")
            landmark = data.get("landmark", "")
            latitude = data.get("latitude")
            longitude = data.get("longitude")

            if not all([address_id, customer_id, first_name, last_name, email, mobile_number, pincode, street]):
                return JsonResponse({"error": "All required fields must be provided.", "status_code": 400}, status=400)

            try:
                customer_address = CustomerAddress.objects.get(id=address_id, customer_id=customer_id)
            except CustomerAddress.DoesNotExist:
                return JsonResponse({"error": "Address not found.", "status_code": 404}, status=404)
            try:
                response = requests.get(f"https://api.postalpincode.in/pincode/{pincode}")
                response_data = response.json()
                if response_data[0]['Status'] == 'Success':
                    post_office_data = response_data[0]['PostOffice'][0]
                    customer_address.village = post_office_data.get('Name', '')
                    customer_address.mandal = post_office_data.get('Block', '')
                    customer_address.postoffice = post_office_data.get('Name', '')
                    customer_address.district = post_office_data.get('District', '')
                    customer_address.state = post_office_data.get('State', '')
                    customer_address.country = post_office_data.get('Country', '')

                    if not latitude or not longitude:
                        geo_params = {
                            "q": f"{pincode},{customer_address.district},{customer_address.state},{customer_address.country}",
                            "format": "json",
                            "limit": 1
                        }
                        geo_headers = {
                            "User-Agent": "MyDjangoApp/1.0 saralkumar.kapilit@gmail.com"
                        }
                        geo_response = requests.get(GEOLOCATION_API_URL, params=geo_params, headers=geo_headers)

                        if geo_response.status_code == 200:
                            geo_data = geo_response.json()
                            if geo_data:
                                latitude = geo_data[0].get("lat", '')
                                longitude = geo_data[0].get("lon", '')
                            else:
                                return JsonResponse({"error": "Failed to fetch latitude and longitude for the provided address.", "status_code": 400}, status=400)
                        else:
                            return JsonResponse({"error": "Geolocation API request failed.", "status_code": geo_response.status_code}, status=geo_response.status_code)
            except Exception as e:
                return JsonResponse({"error": f"Failed to fetch address details: {str(e)}", "status_code": 500}, status=500)

            customer_address.first_name = first_name
            customer_address.last_name = last_name
            customer_address.email = email
            customer_address.mobile_number = mobile_number
            customer_address.alternate_mobile = alternate_mobile
            customer_address.address_type = address_type
            customer_address.pincode = pincode
            customer_address.street = street
            customer_address.landmark = landmark
            customer_address.latitude = latitude
            customer_address.longitude = longitude

            customer_address.save(update_fields=[
                "first_name", "last_name", "email", "mobile_number",
                "alternate_mobile", "address_type", "pincode", "street",
                "landmark", "village", "mandal", "postoffice", 
                "district", "state", "country", "latitude", "longitude"
            ])

            return JsonResponse({
                "message": "Customer address updated successfully.",
                "status_code": 200,
                "address_id": customer_address.id,
                "pincode_details": {
                    "postoffice": customer_address.postoffice,
                    "village": customer_address.village,
                    "mandal": customer_address.mandal,
                    "district": customer_address.district,
                    "state": customer_address.state,
                    "country": customer_address.country,
                    "landmark": customer_address.landmark,
                    "latitude": customer_address.latitude,
                    "longitude": customer_address.longitude
                }
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format.", "status_code": 400}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"An unexpected error occurred: {str(e)}", "status_code": 500}, status=500)

    return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)

@csrf_exempt
def delete_customer_address(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            address_id = data.get("address_id")
            customer_id = data.get("customer_id")

            if not address_id or not customer_id:
                return JsonResponse({"error": "Address ID and Customer ID are required.", "status_code": 400}, status=400)

            try:
                customer_address = CustomerAddress.objects.get(id=address_id, customer_id=customer_id)
                customer_address.delete()
                return JsonResponse({"message": "Customer address deleted successfully.", "status_code": 200}, status=200)
            except CustomerAddress.DoesNotExist:
                return JsonResponse({"error": "Address not found.", "status_code": 404}, status=404)
        
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format.", "status_code": 400}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"An unexpected error occurred: {str(e)}", "status_code": 500}, status=500)

    return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)


@csrf_exempt
def order_product_details(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            product_id = data.get('product_id')
            customer_id = data.get('customer_id')
            quantity = max(int(data.get('quantity', 1)), 1)

            if not customer_id or not product_id:
                return JsonResponse({"error": "customer_id and product_id are required.", "status_code": 400}, status=400)

            try:
                customer = CustomerRegisterDetails.objects.get(id=customer_id)
                product = ProductsDetails.objects.get(id=product_id)
                admin = PavamanAdminDetails.objects.order_by('id').first()

            except CustomerRegisterDetails.DoesNotExist:
                return JsonResponse({"error": "Customer not found.", "status_code": 404}, status=404)
            except ProductsDetails.DoesNotExist:
                return JsonResponse({"error": "Product not found.", "status_code": 404}, status=404)
            except PavamanAdminDetails.DoesNotExist:
                return JsonResponse({"error": "Admin not found.", "status_code": 404}, status=404)

            if not product.category or not product.sub_category:
                return JsonResponse({"error": "Product's category or subcategory is not set.", "status_code": 400}, status=400)

            if "stock" not in product.availability.lower() and "few" not in product.availability.lower():
                return JsonResponse({"error": "Product is out of stock.", "status_code": 400}, status=400)

            if product.quantity < quantity:
                return JsonResponse({"error": "Requested quantity is unavailable.", "status_code": 400}, status=400)

            price = round(float(product.price), 2)
            discount = round(float(product.discount or 0))
            gst = round(float(product.gst or 0))

            # Calculate final price and total price
            discounted_amount = round((price * discount) / 100, 2)
            final_price = round(price - discounted_amount, 2)
            total_price = round(final_price * quantity, 2)


            current_time = datetime.utcnow() + timedelta(hours=5, minutes=30)
            order = OrderProducts.objects.create(
                customer=customer,
                product=product,
                category=product.category,
                sub_category=product.sub_category,
                quantity=quantity,
                price=price,
                discount=discount,  # Add discount here
                gst=gst,
                final_price=final_price,
                order_status="Pending",
                created_at=current_time,
                admin=admin
            )

            image_path = product.product_images[0] if isinstance(product.product_images, list) and product.product_images else None
            image_url = f"{settings.AWS_S3_BUCKET_URL}/{image_path}" if image_path else ""

            return JsonResponse({
                "message": "Order Created successfully!",
                "order_id": order.id,
                "product_name":product.product_name,
                "product_images": image_url,
                "number_of_quantities": quantity,
                "product_price": f"{price:.2f}",
                "discount": f"{discount}%",
                "gst": f"{gst}%",
                "discounted_amount": f"{discounted_amount:.2f}",
                "final_price": f"{final_price:.2f}",                
                "total_price": f"{total_price:.2f}",
                "status_code": 201
            }, status=201)

        except Exception as e:
            return JsonResponse({"error": str(e), "status_code": 500}, status=500)

    return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)


@csrf_exempt
def order_summary(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            order_id = data.get('order_id')
            product_id = data.get('product_id')
            customer_id = data.get('customer_id')
            address_id = data.get('address_id')

            if not all([order_id, product_id, customer_id, address_id]):
                return JsonResponse({"error": "All fields are required.", "status_code": 400}, status=400)

            try:
                order = OrderProducts.objects.get(id=order_id, product_id=product_id, customer_id=customer_id)
                product = ProductsDetails.objects.get(id=product_id)
                customer = CustomerRegisterDetails.objects.get(id=customer_id)
                address = CustomerAddress.objects.get(id=address_id, customer_id=customer_id)
            except OrderProducts.DoesNotExist:
                return JsonResponse({"error": "Order not found.", "status_code": 404}, status=404)
            except ProductsDetails.DoesNotExist:
                return JsonResponse({"error": "Product not found.", "status_code": 404}, status=404)
            except CustomerRegisterDetails.DoesNotExist:
                return JsonResponse({"error": "Customer not found.", "status_code": 404}, status=404)
            except CustomerAddress.DoesNotExist:
                return JsonResponse({"error": "Address not found.", "status_code": 404}, status=404)
            
            image_path = product.product_images[0] if isinstance(product.product_images, list) and product.product_images else None
            image_url = f"{settings.AWS_S3_BUCKET_URL}/{image_path}" if image_path else ""


            return JsonResponse({
                "message": "Order summary fetched successfully!",
                "order_id": order.id,
                "customer_name": f"{address.first_name} {address.last_name}",
                "customer_email": address.email,
                "customer_mobile": address.mobile_number,
                "alternate_customer_mobile": address.mobile_number,
                "product_name": product.product_name,
                "product_price": order.price,
                "quantity": order.quantity,
                "total_price": order.final_price,
                "order_status": order.order_status,
                "order_date": order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "product_images": image_url,
                "shipping_address": {
                    "address_type": address.address_type,
                    "street": address.street,
                    "landmark": address.landmark,
                    "village": address.village,
                    "mandal": address.mandal,
                    "postoffice": address.postoffice,
                    "district": address.district,
                    "state": address.state,
                    "pincode": address.pincode
                },
                "status_code": 200
            }, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e), "status_code": 500}, status=500)

    return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)

@csrf_exempt
def order_multiple_products(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            customer_id = data.get('customer_id')
            products = data.get('products', [])
            from_cart = data.get('from_cart', False)

            if not customer_id or not products:
                return JsonResponse({"error": "customer_id and products are required.", "status_code": 400}, status=400)

            try:
                customer = CustomerRegisterDetails.objects.get(id=customer_id)
                admin = PavamanAdminDetails.objects.order_by('id').first()

            except CustomerRegisterDetails.DoesNotExist:
                return JsonResponse({"error": "Customer not found.", "status_code": 404}, status=404)
            except PavamanAdminDetails.DoesNotExist:
                return JsonResponse({"error": "Admin not found.", "status_code": 404}, status=404)

            successful_orders = []

            for item in products:
                product_id = item.get('product_id')
                quantity = max(int(item.get('quantity', 1)), 1)

                try:
                    product = ProductsDetails.objects.get(id=product_id)
                except ProductsDetails.DoesNotExist:
                    return JsonResponse({"error": "Product not found.", "status_code": 404}, status=404)

                if not product.category or not product.sub_category:
                    return JsonResponse({"error": "Product's category or subcategory is not set.", "status_code": 400}, status=400)

                if "in stock" not in product.availability.lower().strip() and "few" not in product.availability.lower().strip():
                    return JsonResponse({"error": "Product is out of stock.", "status_code": 400}, status=400)
                
                if product.quantity < quantity:
                    return JsonResponse({
                        "error": f"Only {product.quantity} quantity(s) of this product can be added or less.",
                        "status_code": 400
                    }, status=400)

                # if product.quantity < quantity:
                #     return JsonResponse({"error": "Requested quantity is unavailable.", "status_code": 400}, status=400)

                price = float(product.price)
                discount = float(product.discount or 0)
                gst = float(product.gst or 0)
                # final_price = (price - (discount or 0) )* quantity
                discounted_amount = (price * discount) / 100
                final_price = price - discounted_amount
                total_price = round(final_price * quantity, 2)
                

                print(final_price)

                current_time = datetime.utcnow() + timedelta(hours=5, minutes=30)
                order = OrderProducts.objects.create(
                    customer=customer,
                    product=product,
                    category=product.category,
                    sub_category=product.sub_category,
                    quantity=quantity,
                    price=price,
                    final_price=final_price,
                    order_status="Pending",
                    created_at=current_time,
                    admin=admin
                )
                # Cart update - only if not from_cart
                if not from_cart:
                    cart_item, created = CartProducts.objects.get_or_create(
                        customer=customer,
                        product=product,
                        admin=admin,
                        category=product.category,
                        sub_category=product.sub_category,
                        defaults={"quantity": quantity, "added_at": current_time}
                    )

                    if not created:
                        cart_item.quantity += quantity
                        cart_item.save()

                # Save to cart as well
                # cart_item, created = CartProducts.objects.get_or_create(
                #     customer=customer,
                #     product=product,
                #     admin=admin,
                #     category=product.category,
                #     sub_category=product.sub_category,
                #     defaults={"quantity": quantity, "added_at": current_time}
                # )

                # if not created:
                #     cart_item.quantity += quantity
                #     cart_item.save()


                # product.quantity -= quantity
                # product.save()
                image_path = product.product_images[0] if isinstance(product.product_images, list) and product.product_images else None
                image_url = f"{settings.AWS_S3_BUCKET_URL}/{image_path}" if image_path else ""


                successful_orders.append({
                    "order_id": order.id,
                    "product_id": product_id,
                    "product_name": product.product_name,
                    "product_images": image_url,
                    "number_of_quantities": quantity,
                    "product_price": price,
                    "discount_price": round(discounted_amount, 2),
                    "total_price": total_price,
                    "discount":f"{int(product.discount)}%" if product.discount else "0%",
                    "gst": f"{int(gst)}%" if gst else "0%"
                    # "discounted_amount": round(discounted_amount, 2),

                })

            return JsonResponse({
                "message": "Order Created successfully!",
                "orders": successful_orders,
                "status_code": 201
            }, status=201)

        except Exception as e:
            return JsonResponse({"error": str(e), "status_code": 500}, status=500)
    return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)

@csrf_exempt
def multiple_order_summary(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            order_ids = data.get('order_ids')
            product_ids = data.get('product_ids')
            customer_id = data.get('customer_id')
            address_id = data.get('address_id')

            if not all([order_ids, product_ids, customer_id, address_id]):
                return JsonResponse({"error": "order_ids, product_ids, customer_id, and address_id are required.", "status_code": 400}, status=400)

            if len(order_ids) != len(product_ids):
                return JsonResponse({"error": "Mismatch between orders and products count.", "status_code": 400}, status=400)

            try:
                customer = CustomerRegisterDetails.objects.get(id=customer_id)
                address = CustomerAddress.objects.get(id=address_id, customer_id=customer_id)
                
                CustomerAddress.objects.filter(customer_id=customer_id).update(select_address=False)  #Unselect all
                address.select_address = True
                address.save()
            
            except CustomerRegisterDetails.DoesNotExist:
                return JsonResponse({"error": "Customer not found.", "status_code": 404}, status=404)
            except CustomerAddress.DoesNotExist:
                return JsonResponse({"error": "Address not found.", "status_code": 404}, status=404)

            order_list = []

            for order_id, product_id in zip(order_ids, product_ids):
                try:
                    order = OrderProducts.objects.get(id=order_id, product_id=product_id, customer_id=customer_id)
                    product = ProductsDetails.objects.get(id=product_id)
                    price = float(product.price)
                    discount = float(product.discount or 0)
                    discounted_amount = (price * discount) / 100
                    final_price = price - discounted_amount
                    image_path = product.product_images[0] if isinstance(product.product_images, list) and product.product_images else None
                    image_url = f"{settings.AWS_S3_BUCKET_URL}/{image_path}" if image_path else ""


                    
                    order_list.append({
                        "order_id": order.id,
                        "order_name": f"Order {order.id}",
                        "customer_name": f"{address.first_name} {address.last_name}",
                        "customer_email": address.email,
                        "customer_mobile": address.mobile_number,
                        "alternate_customer_mobile": address.mobile_number,
                        "product_name": product.product_name,
                        "product_id":product_id,
                        "product_price": order.price,
                        "quantity": order.quantity,
                        "discount":f"{int(discount)}%" if discount else "0%",
                        "gst": f"{int(product.gst or 0)}%",
                        "final_price": round(final_price, 2),
                        # "discount_price": (float(product.price)-float(product.discount or 0)),
                        "total_price": order.final_price,
                        "order_status": order.order_status,
                        "order_date": order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                        "product_images": image_url,
                    })

                except OrderProducts.DoesNotExist:
                    product_name = ProductsDetails.objects.filter(id=product_id).values_list('product_name', flat=True).first() or f"Product {product_id}"
                    return JsonResponse({"error": f"Order {order_id} with product '{product_name}' not found.", "status_code": 404}, status=404)
                except ProductsDetails.DoesNotExist:
                    return JsonResponse({"error": f"Product with ID {product_id} not found.", "status_code": 404}, status=404)

            shipping_address = {
                "address_id":address.id,
                "customer_name": f"{address.first_name} {address.last_name}",
                "select_address":address.select_address,
                "address_type": address.address_type,
                "street": address.street,
                "landmark": address.landmark,
                "village": address.village,
                "mandal": address.mandal,
                "postoffice": address.postoffice,
                "district": address.district,
                "state": address.state,
                "pincode": address.pincode
            }
            
            return JsonResponse({
                "message": "Multiple order summaries fetched successfully!",
                "orders": order_list,
                "shipping_address": shipping_address,
                "status_code": 200
            }, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e), "status_code": 500}, status=500)
    return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)



razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

@csrf_exempt
def create_razorpay_order(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            customer_id = data.get('customer_id')
            order_products = data.get('order_products', [])  # Expecting [{"order_id": 1, "product_id": 2}, ...]

            if not customer_id or not order_products:
                return JsonResponse({"error": "customer_id and order_products are required.", "status_code": 400}, status=400)

            try:
                customer = CustomerRegisterDetails.objects.get(id=customer_id)
            except CustomerRegisterDetails.DoesNotExist:
                return JsonResponse({"error": "Customer not found.", "status_code": 404}, status=404)
           
            try:
                address = CustomerAddress.objects.get(customer_id=customer_id, select_address=True)
                address_id = address.id
            except CustomerAddress.DoesNotExist:
                return JsonResponse({
                    "error": "No selected address found for the customer. Please select an address first.",
                    "status_code": 404
                }, status=404)

            total_amount = 0
            valid_orders = []
            order_ids = [] 
            product_ids = [] 
        
            for item in order_products:
                order_id = item.get('order_id')
                product_id = item.get('product_id')

                try:
                    order = OrderProducts.objects.get(id=order_id, customer=customer, product_id=product_id)
                    total_amount += order.final_price
                    order_ids.append(str(order.id))  
                    product_ids.append(str(order.product.id)) 
                    
                    valid_orders.append({
                        "order_id": order.id,
                        "product_id": order.product.id,
                        "product_name": order.product.product_name,
                        "category": order.category,
                        "sub_category": order.sub_category,
                        "quantity": order.quantity,
                        "amount": float(order.price),
                        "total_price": order.final_price,
                        "order_status": order.order_status
                    })
                except OrderProducts.DoesNotExist:
                    return JsonResponse({"error": f"Order ID {order_id} with Product ID {product_id} not found or does not belong to the customer.", "status_code": 404}, status=404)

            if total_amount <= 0:
                return JsonResponse({"error": "Total amount must be greater than zero.", "status_code": 400}, status=400)
          
            formatted_time = datetime.utcnow().strftime("%Y%m%d%H%M%S%f") 
            receipt_id = f"order_{customer_id}_{formatted_time}"
           
            # Create Razorpay Order
            razorpay_order = razorpay_client.order.create({
                "amount": int(total_amount * 100),  # Convert to paisa
                "currency": "INR",
                "receipt": receipt_id,
                "payment_capture": 1,  # Auto capture payment
                
                "notes": {  
                    "order_ids": ",".join(order_ids), 
                    "product_ids": ",".join(product_ids),  
                    "customer_id": str(customer.id),
                    "address_id": str(address_id) 
                }

            })
          
            callback_url = "http://127.0.0.1:8000/razorpay-callback"

            return JsonResponse({
                "message": "Razorpay Order Created Successfully!",
                "razorpay_key": settings.RAZORPAY_KEY_ID,  # Sending Razorpay public key
                "razorpay_order_id": razorpay_order["id"],
                "callback_url": callback_url,
                "customer_id": customer.id,
                "address_id":address_id,
                "total_amount": total_amount,
                "orders": valid_orders,
                "status_code": 201
            }, status=201)

        except Exception as e:
            return JsonResponse({"error": str(e), "status_code": 500}, status=500)

    return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)


@csrf_exempt
def razorpay_callback(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))

        required_fields = ["razorpay_payment_id", "razorpay_order_id", "razorpay_signature", "customer_id", "order_products","address_id"]
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            return JsonResponse({"error": f"Missing required fields: {', '.join(missing_fields)}", "status_code": 400}, status=400)

        # Extract Data
        razorpay_payment_id = data["razorpay_payment_id"]
        razorpay_order_id = data["razorpay_order_id"]
        razorpay_signature = data["razorpay_signature"]
        customer_id = data["customer_id"]
        order_products = data["order_products"]  # Expecting a list of {order_id, product_id}
        address_id =data["address_id"]
        
        if not isinstance(order_products, list) or not order_products:
            return JsonResponse({"error": "Invalid or missing order_products. It must be a list of order-product mappings.", "status_code": 400}, status=400)

        # Verify Razorpay Signature
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        params = {
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature,
        }

        try:
            client.utility.verify_payment_signature(params)

            # Fetch Payment Details from Razorpay
            payment_details = client.payment.fetch(razorpay_payment_id)
            payment_status = payment_details.get("status", "failed")
            payment_mode = payment_details.get("method", "unknown")
            transaction_id = payment_details.get("id", razorpay_payment_id)
            
            # Fetch Orders using order IDs and Product IDs
            order_list = []
            for item in order_products:
                order_id = item.get("order_id")
                product_id = item.get("product_id")

                if not order_id or not product_id:
                    return JsonResponse({"error": "Each item in order_products must contain order_id and product_id.", "status_code": 400}, status=400)

                order = OrderProducts.objects.filter(id=order_id, product_id=product_id, customer_id=customer_id).first()
                if order:
                    order_list.append(order)

            if not order_list:
                return JsonResponse({"error": "No matching orders found for this payment.", "status_code": 404}, status=404)

            if payment_status == "captured":
                # Initialize lists to store multiple IDs
                order_product_ids = []
                category_ids = []
                sub_category_ids = []
                product_ids = []
                total_quantity = 0
                total_amount = 0

                first_order = None  # Reference for ForeignKey relations

                for order in order_list:
                    order.order_status = "Paid"
                    order.save(update_fields=["order_status"])
                    
                    # Reduce the stock of the product
                    product = order.product
                    if product.quantity >= order.quantity:
                        product.quantity -= order.quantity  # Reduce the quantity
                    else:
                        product.quantity = 0  # Ensure stock doesn't go negative
                   
                    if product.quantity<= 10 and product.quantity!=0 and product.quantity<0:
                       product.availability= "Very Few Products Left"
                    elif product.quantity== 0:
                       product.availability= "Out of Stock"
                    else:
                       product.availability="In Stock"
                    product.save(update_fields=["quantity","availability"])  # Save changes to the product
                    
                    if not first_order:
                        first_order = order  # Use first order as a reference
                    
                    # Append IDs to lists
                    order_product_ids.append(order.id)
                    category_ids.append(order.product.category.id)
                    sub_category_ids.append(order.product.sub_category.id)
                    product_ids.append(order.product.id)

                    # Calculate totals
                    total_quantity += order.quantity
                    total_amount += order.final_price
                try:
                    customer_address = CustomerAddress.objects.get(id=address_id, customer_id=customer_id)
                except CustomerAddress.DoesNotExist:
                    return JsonResponse({
                        "error": "Invalid address_id. No such address found for this customer.",
                        "status_code": 404
                    }, status=404)

                if first_order:
                    product_order_id = f"PROD{datetime.now().strftime('%Y%m%d%H%M%S')}{''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}"
                    
                    # Generate custom invoice number
                    today = timezone.now().date()
                    date_str = today.strftime("%d%m%Y")
                    prefix = "PVM"
                    base_invoice = f"{prefix}{date_str}"

                    latest_invoice = PaymentDetails.objects.filter(created_at__date=today).order_by('-id').first()
                    if latest_invoice and latest_invoice.invoice_number:
                       last_serial = int(latest_invoice.invoice_number[-4:])
                    else:
                        last_serial = 0

                    new_serial = last_serial + 1
                    new_invoice_number = f"{base_invoice}{str(new_serial).zfill(4)}"

                    # Save Payment Details using JSON fields
                    PaymentDetails.objects.create(
                        admin=first_order.product.admin,
                        customer=first_order.customer,
                        # customer_address=CustomerAddress.objects.filter(customer=first_order.customer).first(),
                        customer_address=customer_address,
                        category_ids=category_ids,  # Store list directly
                        sub_category_ids=sub_category_ids,  # Store list directly
                        product_ids=product_ids,  # Store list directly
                        order_product_ids=order_product_ids,  # Store list directly
                        razorpay_order_id=razorpay_order_id,
                        razorpay_payment_id=razorpay_payment_id,
                        razorpay_signature=razorpay_signature,
                        amount=total_amount,
                        total_amount=total_amount,
                        payment_type="online",
                        payment_mode=payment_mode,
                        transaction_id=transaction_id,
                        quantity=total_quantity,
                        product_order_id= product_order_id, 
                        invoice_number=new_invoice_number,
                    )

                    # Get all paid products for the customer
                    paid_product_ids = OrderProducts.objects.filter(
                        customer_id=customer_id, order_status="Paid"
                    ).values_list("product_id", flat=True)

                    # Remove products from CartOrder if they exist there
                    CartProducts.objects.filter(product_id__in=paid_product_ids, customer_id=customer_id).delete()
                    
                    product_list = []

                    for order in order_list:
                        try:
                            product_details = ProductsDetails.objects.get(id=order.product.id)

                            # Take only the first image from the list if available
                            # image_url = (
                            #     request.build_absolute_uri(product_details.product_images[0])
                            #     if isinstance(product_details.product_images, list) and product_details.product_images
                            #     else ""
                            # )
                            image_path = product_details.product_images[0] if isinstance(product_details.product_images, list) and product_details.product_images else None
                            image_url = f"{settings.AWS_S3_BUCKET_URL}/{image_path}" if image_path else ""


                            product_name = product_details.product_name

                        except ProductsDetails.DoesNotExist:
                            image_url = ""
                            product_name = "Product Not Found"

                        product_list.append({
                            "image_url": image_url,
                            "name": product_name,
                            "quantity": order.quantity,
                            "price": order.final_price,
                        })

                    send_html_order_confirmation(
                        to_email=first_order.customer.email,
                        customer_name=f"{first_order.customer.first_name} {first_order.customer.last_name}",
                        product_list=product_list,
                        total_amount=total_amount,
                        order_id=product_order_id,
                        transaction_id=transaction_id,
                        # delivery_date=(datetime.now() + timedelta(days=3)).strftime('%a, %b %d, %Y')
                    )
                    
                    # Send SMS to the customer
                                  
                    mobile_no = first_order.customer.mobile_no
                    # sms_message = f"Dear {first_order.customer.first_name} {first_order.customer.last_name},\nYour order with ID {product_order_id} has been successfully placed. Total Amount: ₹{total_amount}. Thank you for shopping with us!"
                    sms_message = (
                        f"Dear {first_order.customer.first_name} {first_order.customer.last_name},\n"
                        f"Your order (ID: {product_order_id}) has been confirmed and payment was successful."
                        f"Total Amount: ₹{total_amount}.\nThank you for shopping with us!"
                    )

                    try:
                        send_bulk_sms([mobile_no], sms_message)  # Pass the mobile number as a list
                    except Exception as e:
                        return JsonResponse({"error": f"Failed to send SMS: {str(e)}", "status_code": 500}, status=500)


                    return JsonResponse({
                        "message": "Payment successful for all orders!",
                        "razorpay_order_id": razorpay_order_id,
                        "customer_id": customer_id,
                        "total_orders_paid": len(order_product_ids),
                        "payment_mode": payment_mode,
                        "transaction_id": transaction_id,
                        "total_amount": total_amount,
                        "order_product_ids": order_product_ids,  
                        "category_ids": category_ids,  
                        "sub_category_ids": sub_category_ids, 
                        "product_order_id": product_order_id,
                        "invoice_number": new_invoice_number,
                        "product_ids": product_ids,
                        "status_code": 200
                    }, status=200)

            else:
                OrderProducts.objects.filter(id__in=[order.id for order in order_list]).update(order_status="Failed")
                return JsonResponse({"error": "Payment failed.", "razorpay_order_id": razorpay_order_id, "status_code": 400}, status=400)

        except razorpay.errors.SignatureVerificationError:
            OrderProducts.objects.filter(id__in=[order.id for order in order_list]).update(order_status="Failed")
            return JsonResponse({"error": "Signature verification failed.", "razorpay_order_id": razorpay_order_id, "status_code": 400}, status=400)

    except Exception as e:
        return JsonResponse({"error": str(e), "status_code": 500}, status=500)


def send_html_order_confirmation(to_email, customer_name, product_list, total_amount, order_id, transaction_id):
    subject = "🧾 Order Confirmation - Payment Successful"

    product_html = ""
    for product in product_list:
        # delivery_date = product.get('delivery_date', 'Soon')  # Default to 'Soon' if not provided
        product_images = product.get('product_images', [])
        image_url = ""

        if product_images:
            image_url = f"{settings.AWS_S3_BUCKET_URL}/{product_images[0]}"  # Get the first image URL if available



        product_html += f"""
        <tr>
            <td style="padding: 10px;">
                <img src="{image_url}" width="80" height="80" style="border-radius: 5px;" />

            </td>
            <td style="padding: 10px;">
                <strong>{product['name']}</strong><br>
                Qty: {product['quantity']}<br>
                Price: ₹{product['price']}
            </td>
        </tr>
        """

    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; border: 1px solid #ddd; padding: 20px; border-radius: 10px;">
        <h2 style="color: #2E7D32;">Payment Successful!</h2>
        <p>Hi {customer_name},</p>
        <p>Thank you for your order. Your payment was successful.</p>

        <p><strong>Order ID:</strong> {order_id}<br>
        <strong>Transaction ID:</strong> {transaction_id}<br>
        <strong>Total Amount Paid:</strong> ₹{total_amount}</p>

        <h3 style="border-bottom: 1px solid #ddd; padding-bottom: 5px;">Your Products</h3>
        <table style="width: 100%; border-collapse: collapse;">
            {product_html}
        </table>

        <p style="margin-top: 20px;">We’ll send you another update when your products are out for delivery.</p>

        <p>Regards,<br>Pavaman Team</p>
    </div>
    """

    try:
        email = EmailMessage(
            subject=subject,
            body=html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to_email]
        )
        email.content_subtype = "html"  # Send as HTML
        email.send(fail_silently=False)
        return True
    except Exception as e:
        print(f"[Email Error] {e}")
        return False


@csrf_exempt
def cancel_order(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            order_id = data.get('order_id')
            customer_id = data.get('customer_id')
            product_id = data.get('product_id')

            if not all([order_id, customer_id, product_id]):
                return JsonResponse({"error": "order_id, customer_id, and product_id are required.", "status_code": 400}, status=400)

            try:
                order = OrderProducts.objects.get(id=order_id, customer_id=customer_id, product_id=product_id)
                product = order.product
            except OrderProducts.DoesNotExist:
                return JsonResponse({"error": "Order not found or does not belong to the given customer and product.", "status_code": 404}, status=404)

            product.quantity += order.quantity
            product.save()

            order.delete()

            return JsonResponse({
                "message": "Order cancelled successfully!",
                "order_id": order_id,
                "product_id": product_id,
                "customer_id": customer_id,
                "restored_quantity": order.quantity,
                "product_name": product.product_name,
                "status_code": 200
            }, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e), "status_code": 500}, status=500)
    return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)

@csrf_exempt
def cancel_multiple_orders(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            customer_id = data.get('customer_id')
            orders = data.get('orders', [])
            print("Received Data:", data) 
            if not customer_id or not orders:
                return JsonResponse({"error": "customer_id and orders are required.", "status_code": 400}, status=400)

            successful_cancellations = []

            for item in orders:
                order_id = item.get('order_id')
                product_id = item.get('product_id')

                if not order_id or not product_id:
                    return JsonResponse({"error": "order_id and product_id are required for each order.", "status_code": 400}, status=400)

                try:
                    order = OrderProducts.objects.get(id=order_id, customer_id=customer_id, product__id=product_id)
                    product = order.product
                except OrderProducts.DoesNotExist:
                    return JsonResponse({"error": f"Orders not found for customer and product.", "status_code": 404}, status=404)

                product.quantity += order.quantity
                product.save()

                order.delete()

                successful_cancellations.append({
                    "order_id": order_id,
                    "product_id": product_id,
                    "restored_quantity": order.quantity,
                    "product_name": product.product_name
                })

            return JsonResponse({
                "message": "Selected orders cancelled successfully!",
                "cancelled_orders": successful_cancellations,
                "status_code": 200
            }, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e), "status_code": 500}, status=500)
    return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)

def get_category_and_subcategory_product_counts(category_id,category_name):
    try:
        category= CategoryDetails.objects.get(id=category_id,category_name=category_name,category_status=1)
        subcategories=SubCategoryDetails.objects.filter(category=category,sub_category_status=1)
        total_category_product_count = 0
        subcategory_list=[]
        for subcategory in subcategories:
            subcategory_product_count=ProductsDetails.objects.filter(sub_category=subcategory,product_status=1).count()
            total_category_product_count +=subcategory_product_count #add to all subcategory product count

            subcategory_list.append({
                "sub_category_id":str(subcategory.id),
                "sub_category_name":subcategory.sub_category_name,
                "product_count":subcategory_product_count
            })
        return{
            "category_id":str(category.id),
            "category_name":category.category_name,
            "total_category_product_count": total_category_product_count,
            "subcategories":subcategory_list
        }
    except CategoryDetails.DoesNotExist:
        return None  # Return None if category does not exist

@csrf_exempt
def view_category_and_subcategory_product_counts(request):
    if request.method =="POST":
        try:
            data = json.loads(request.body.decode('utf-8'))
            category_id=data.get('category_id')
            category_name = data.get('category_name')

            if not category_id or not category_name:
                return JsonResponse({"error":"category_id and category_name are required.", "status_code": 400}, status=400)

            category_data=get_category_and_subcategory_product_counts(category_id,category_name)
            if category_data:
                return JsonResponse({
                    "message":"Data retrieved successfully.",

                    "categories":[category_data]
                },status=200)
            else:
                return JsonResponse({"error": "Category not found.", "status_code": 404}, status=404)
        
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format.", "status_code": 400}, status=400)
        except Exception as e:
            return JsonResponse({"error":str(e),"status_code":500},status=500)
    return JsonResponse({"error":"Invalid Request menthod","status_code":405},status=405)


#this is for subcatagory page

@csrf_exempt
def filter_product_price_each_category(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode('utf-8'))
            category_id = data.get("category_id")
            category_name = data.get("category_name")
            customer_id = data.get("customer_id")
            min_price = data.get("min_price")  # Get min price from request
            max_price = data.get("max_price")  # Get max price from request

            if not category_id or not category_name:
                return JsonResponse({"error": "category_id and category_name are required.", "status_code": 400}, status=400)

            try:
                category = CategoryDetails.objects.get(id=category_id)
            except CategoryDetails.DoesNotExist:
                return JsonResponse({"error": "Invalid category_id. Category not found.", "status_code": 404}, status=404)

            if category.category_name != category_name:
                return JsonResponse({"error": "category_name does not match the given category_id.", "status_code": 400}, status=400)

            subcategories = SubCategoryDetails.objects.filter(category_id=category_id, sub_category_status=1)

            subcategories_list = []

            for subcategory in subcategories:
                # Fetch products under the current subcategory within the given price range
                products_query = ProductsDetails.objects.filter(
                    category_id=category_id,
                    sub_category_id=subcategory.id,
                    product_status=1
                )

                # Apply price filter if min_price and max_price are provided
                if min_price is not None:
                    products_query = products_query.filter(price__gte=min_price)
                if max_price is not None:
                    products_query = products_query.filter(price__lte=max_price)

                products_list = []
                for product in products_query:
                    price = float(product.price)
                    discount = float(product.discount or 0)
                    discounted_amount = (price * discount) / 100
                    final_price = price - discounted_amount
                    image_path = product.product_images[0] if isinstance(product.product_images, list) and product.product_images else None
                    image_url = f"{settings.AWS_S3_BUCKET_URL}/{image_path}" if image_path else ""


                    product_data = {
                        "product_id": str(product.id),
                        "product_name": product.product_name,
                        "sku_number": product.sku_number,
                        "price": float(product.price),
                        "gst": f"{int(product.gst or 0)}%",
                        # "discount": float(product.discount or 0),
                        # "final_price": float(product.price) - float(product.discount or 0),
                        "discount":f"{int(discount)}%" if discount else "0%",
                        "final_price": round(final_price),
                        "availability": product.availability,
                        "quantity": product.quantity,
                        "product_image_url": image_url,
                        "cart_status": product.cart_status
                    }
                    products_list.append(product_data)

                subcategories_list.append({
                    "sub_category_id": subcategory.id,
                    "sub_category_name": subcategory.sub_category_name,
                    "products": products_list
                })

            # Fetch overall price range for the category
            all_products = ProductsDetails.objects.filter(category_id=category_id, product_status=1)

            if not all_products.exists():
                return JsonResponse({"error": "No products found for the given category.", "status_code": 404}, status=404)

            price_range = all_products.aggregate(
                min_price=Min("price"),
                max_price=Max("price")
            )
            if price_range["min_price"] == price_range["max_price"]:
                price_range["min_price"] = 0

            response_data = {
                "message": "Price range retrieved successfully.",
                "category_id": category_id,
                "category_name": category_name,
                # "gst": f"{int(product.gst or 0)}%",
                "min_price": price_range["min_price"],
                "max_price": price_range["max_price"],
                "sub_categories": subcategories_list,  # Subcategory-wise product data
                "status_code": 200
            }

            if customer_id:
                response_data["customer_id"] = customer_id

            return JsonResponse(response_data, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format.", "status_code": 400}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e), "status_code": 500}, status=500)

    return JsonResponse({"error": "Invalid request method.", "status_code": 405}, status=405)


#this is for product page

@csrf_exempt
def filter_product_price(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode('utf-8'))
            category_id = data.get("category_id")
            category_name = data.get("category_name")
            subcategory_id = data.get("sub_category_id")
            sub_category_name = data.get("sub_category_name")
            customer_id = data.get("customer_id")
            min_price = data.get("min_price")  # Get min price from request
            max_price = data.get("max_price")  # Get max price from request

            if not category_id or not category_name:
                return JsonResponse({"error": "category_id and category_name are required.", "status_code": 400}, status=400)

            if not subcategory_id or not sub_category_name:
                return JsonResponse({"error": "sub_category_id and sub_category_name are required.", "status_code": 400}, status=400)

            try:
                category = CategoryDetails.objects.get(id=category_id)
                if category.category_name != category_name:
                    return JsonResponse({"error": "Incorrect category_name for the given category_id.", "status_code": 400}, status=400)
            except CategoryDetails.DoesNotExist:
                return JsonResponse({"error": "Invalid category_id. Category not found.", "status_code": 404}, status=404)

            try:
                subcategory = SubCategoryDetails.objects.get(id=subcategory_id, category_id=category_id, sub_category_status=1)
                if subcategory.sub_category_name != sub_category_name:
                    return JsonResponse({"error": "Incorrect sub_category_name for the given sub_category_id.", "status_code": 400}, status=400)
            except SubCategoryDetails.DoesNotExist:
                return JsonResponse({"error": "Invalid sub_category_id for the given category.", "status_code": 404}, status=404)

            products_query = ProductsDetails.objects.filter(
                category_id=category_id,
                sub_category_id=subcategory_id,
                product_status=1
            )

            # Apply price filter if min_price and max_price are provided
            if min_price is not None and isinstance(min_price, (int, float)):
                products_query = products_query.filter(price__gte=min_price)

            if max_price is not None and isinstance(max_price, (int, float)):
                products_query = products_query.filter(price__lte=max_price)
           
            products_list = []
            for product in products_query:
                price = float(product.price)
                discount = float(product.discount or 0)
                discounted_amount = (price * discount) / 100
                final_price = price - discounted_amount
                image_path = product.product_images[0] if isinstance(product.product_images, list) and product.product_images else None
                image_url = f"{settings.AWS_S3_BUCKET_URL}/{image_path}" if image_path else ""


                product_data = {
                    "product_id": str(product.id),
                    "product_name": product.product_name,
                    "sku_number": product.sku_number,
                    "price": float(product.price),
                    # "discount": float(product.discount or 0),
                    # "final_price": float(product.price) - float(product.discount or 0),
                    "discount":f"{int(discount)}%" if discount else "0%",
                    "gst": f"{int(product.gst or 0)}%",
                    "final_price": round(final_price),
                    "availability": product.availability,
                    "quantity": product.quantity,
                    "product_image_url": image_url,
                    "cart_status": product.cart_status
                }
                products_list.append(product_data)

           
            if not products_list:
                return JsonResponse({"error": "No products found within the specified price range.", "status_code": 404}, status=404)

            # Get min and max price for the given subcategory (based on the filtered products)
            price_range = products_query.aggregate(
                min_price=Min("price"),
                max_price=Max("price")
            )
            if price_range["min_price"] == price_range["max_price"]:
                price_range["min_price"] = 0

            response_data = {
                "message": "Filtered products retrieved successfully.",
                "category_id": category_id,
                "category_name": category.category_name, 
                "sub_category_id": subcategory_id,
                "sub_category_name": subcategory.sub_category_name,  
                "min_price": price_range["min_price"],
                "max_price": price_range["max_price"],
                "products": products_list, 
                "status_code": 200
            }

            if customer_id:
                response_data["customer_id"] = customer_id

            return JsonResponse(response_data, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format.", "status_code": 400}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e), "status_code": 500}, status=500)

    return JsonResponse({"error": "Invalid request method.", "status_code": 405}, status=405)

@csrf_exempt
def sort_products_inside_subcategory(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode('utf-8'))
            sub_category_id = data.get("sub_category_id")
            sub_category_name = data.get("sub_category_name")
            sort_by = data.get("sort_by")  # Sorting type

            customer_id = request.session.get("customer_id") or data.get("customer_id")

            if not all([sub_category_id, sub_category_name, sort_by]):
                return JsonResponse({
                    "error": "sub_category_id, sub_category_name, and sort_by are required.",
                    "status_code": 400
                }, status=400)

            sub_category = SubCategoryDetails.objects.filter(id=sub_category_id, sub_category_name=sub_category_name, sub_category_status=1).first()
            if not sub_category:
                return JsonResponse({"error": "Subcategory not found.", "status_code": 404}, status=404)

            if sort_by == "latest":
                order_by_field = "-created_at"  # Newest first
            elif sort_by == "low_to_high":
                order_by_field = "price"  # Price ascending
            elif sort_by == "high_to_low":
                order_by_field = "-price"  # Price descending
            else:
                return JsonResponse({"error": "Invalid sort_by value. Use 'latest', 'low_to_high', or 'high_to_low'.", "status_code": 400}, status=400)

            products = ProductsDetails.objects.filter(
                sub_category=sub_category, product_status=1
            ).order_by(order_by_field)

            if not products.exists():
                return JsonResponse({"error": "No products found for the given sub category.", "status_code": 404}, status=404)
           
            # Get min and max price
            # price_range = products.aggregate(
            #     product_min_price=Min("price"),
            #     product_max_price=Max("price")
            # )

            all_prices = []
            for product in products:
                price = float(product.price)
                gst = float(product.gst)
                discount = float(product.discount or 0)

                discounted_amount = (price * discount) / 100
                final_price = price - discounted_amount

                all_prices.append(int(final_price))
            
            min_price = min(all_prices)
            max_price = max(all_prices)

            if min_price == max_price:
                min_price = 0

            price_range = {
                "product_min_price": min_price,
                "product_max_price": max_price
            }
            # price_range = {
            #     "product_min_price": min(all_prices),
            #     "product_max_price": max(all_prices)
            # }

            response_data = {
                "message": f"Products sorted by {sort_by.replace('_', ' ')} successfully.",
                "status_code": 200,
                "sub_category_id": str(sub_category.id),
                "sub_category_name": sub_category_name,
                "product_min_price": price_range["product_min_price"],
                "product_max_price": price_range["product_max_price"],
                "products": format_product_list(products)
            }

            if customer_id:
                response_data["customer_id"] = str(customer_id)

            return JsonResponse(response_data, status=200)

        except Exception as e:
            return JsonResponse({"error": f"An unexpected error occurred: {str(e)}", "status_code": 500}, status=500)

    return JsonResponse({"error": "Invalid request method. Use POST.", "status_code": 405}, status=405)


def format_product_list(products):

    #Helper function to format product details.
    return [
        {
            "product_id": str(product.id),
            "product_name": product.product_name,
            "sku_number": product.sku_number,
            "price": round(float(product.price),2)  ,
            
            "gst": f"{int(product.gst or 0)}%",
            "discount":f"{int(product.discount)}%" if product.discount else "0%",
            
            "final_price": round(float(product.price) - (float(product.price) * float(product.discount or 0) / 100), 2),
            "availability": product.availability,
            "quantity": product.quantity,
            "product_image_url": (
                f"{settings.AWS_S3_BUCKET_URL}/{product.product_images[0]}"
                if isinstance(product.product_images, list) and product.product_images
                else ""
            ),
            "cart_status": product.cart_status
        }
        for product in products
    ]

@csrf_exempt
def get_customer_details_by_admin(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            admin_id = data.get("admin_id")

            if not admin_id:
                return JsonResponse({"error": "admin_id is required.", "status_code": 400}, status=400)

            customers = CustomerRegisterDetails.objects.filter(admin_id=admin_id).values(
                "id", "first_name", "last_name", "email", "mobile_no", "account_status","created_on","register_type","register_status"
            )

            customers_list = list(customers)

            if not customers_list:
                return JsonResponse({"error": "No matching customer found.", "status_code": 404}, status=404)
        
            activated_count = sum(1 for c in customers_list if c["account_status"] == 1)
            inactivated_count = sum(1 for c in customers_list if c["account_status"] == 0)
            total_count = activated_count + inactivated_count

            response_data = {
                "status": "success",
                "customers": customers_list,
                "activated_count": activated_count,
                "inactivated_count": inactivated_count,
                "total_count": total_count,
                "status_code": 200
            }
            if admin_id:
                response_data["admin_id"] = str(admin_id)
            return JsonResponse(response_data, status=200)
           
            # return JsonResponse({"status": "success", "customers": customers_list,"activated_count": activated_count,"inactivated_count": inactivated_count,"total_count": total_count, "status_code": 200}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format.", "status_code": 400}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"An unexpected error occurred: {str(e)}", "status_code": 500}, status=500)

    return JsonResponse({"error": "Invalid request method. Only POST is allowed.", "status_code": 405}, status=405)


@csrf_exempt
def customer_search_categories(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            customer_id = data.get('customer_id')
            search_query = data.get('category_name', '').strip()  # Get search term

            if not search_query:
                return JsonResponse({"error": "Atleast one character is required.", "status_code": 400}, status=400)

            categories = CategoryDetails.objects.filter(
                
                category_status=1,
                category_name__icontains=search_query
            )
            if not categories.exists():
                response_data = {"message": "No category details found", "status_code": 200}
                if customer_id:
                    response_data["customer_id"] = customer_id  # Include customer_id if available
                return JsonResponse(response_data, status=200)  


            category_list = [
                {
                    "category_id": str(category.id),
                    "category_name": category.category_name,
                    "category_image_url": f"{settings.AWS_S3_BUCKET_URL}/{category.category_image.replace('\\', '/')}" if category.category_image else ""
                }
                for category in categories
            ]

            response_data = {
                "message": "Categories retrieved successfully.",
                "categories": category_list,
                "status_code": 200
            }
            if customer_id:
                response_data["customer_id"] = str(customer_id)
            return JsonResponse(response_data, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data.", "status_code": 400}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"An unexpected error occurred: {str(e)}", "status_code": 500}, status=500)

    return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)


@csrf_exempt
def customer_search_subcategories(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            customer_id = data.get('customer_id')
            category_id = data.get('category_id')
            sub_category_name = data.get('sub_category_name', '').strip()
         
            if not category_id:
                return JsonResponse({"error": "Category Id is required.", "status_code": 400}, status=400)

            if sub_category_name == "": 
                return JsonResponse({"error": "Atleast one character is required.", "status_code": 400}, status=400)

            subcategories = SubCategoryDetails.objects.filter(
                category_id=category_id,
                sub_category_status=1,
                sub_category_name__icontains=sub_category_name  # Partial match
            )
           
            if not subcategories.exists():
                response_data = {"message": "No subcategory details found", "status_code": 200}
                if customer_id:
                    response_data["customer_id"] = customer_id  # Include customer_id if available
                return JsonResponse(response_data, status=200)           

            subcategory_list = [
    {
        "sub_category_id": str(subcategory.id),
        "sub_category_name": subcategory.sub_category_name,
        "sub_category_image": f"{settings.AWS_S3_BUCKET_URL}/{subcategory.sub_category_image.replace('\\', '/')}" if subcategory.sub_category_image else "",
        "category_id": str(subcategory.category_id)
    }
    for subcategory in subcategories
]
            response_data = {
                "message": "Subcategories retrieved successfully.",
                "categories": subcategory_list,
                "status_code": 200
            }
            if customer_id:
                response_data["customer_id"] = str(customer_id)
            return JsonResponse(response_data, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data.", "status_code": 400}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"An unexpected error occurred: {str(e)}", "status_code": 500}, status=500)

    return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)

@csrf_exempt
def customer_search_products(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            customer_id = data.get('customer_id')
            category_id = data.get('category_id')
            sub_category_id = data.get('sub_category_id')
            product_name = data.get('product_name', '').strip()  # Optional search term

            if not category_id:
                return JsonResponse({"error": "Category ID are required.", "status_code": 400}, status=400)
            if not sub_category_id:
                return JsonResponse({"error": "Sub Category ID are required.", "status_code": 400}, status=400)

            if product_name == "":
                return JsonResponse({"error": "Atleast one character is required.", "status_code": 400}, status=400)

            products = ProductsDetails.objects.filter(
                
                category_id=category_id,
                sub_category_id=sub_category_id,
                product_status=1
            )
            if product_name:
                products = products.filter(product_name__icontains=product_name)


            if not products.exists():
                response_data = {"message": "No products details found", "status_code": 200}
                if customer_id:
                    response_data["customer_id"] = customer_id  # Include customer_id if available
                return JsonResponse(response_data, status=200)    

            product_list = []
            for product in products:
                product_images = product.product_images
                if isinstance(product_images, list):
                    product_image_url = (
                         f"{settings.AWS_S3_BUCKET_URL}/{product_images[0].replace('\\', '/')}"
                        if product_images else ""
                    )
                elif isinstance(product_images, str):
                      product_image_url = f"{settings.AWS_S3_BUCKET_URL}/{product_images.replace('\\', '/')}"
                else:
                    product_image_url = ""      

                product_list.append({
                    "category_id": str(product.category_id),
                    "sub_category_id": str(product.sub_category_id),
                    "product_id": str(product.id),
                    "product_name": product.product_name,       
                    "product_image_url": product_image_url,
                    "sku_number": product.sku_number,
                    "price": float(product.price),
                    "gst": f"{int(product.gst or 0)}%",
                    # "discount": float(product.discount or 0),
                    # "final_price": float(product.price) - float(product.discount or 0),
                    "discount":f"{int(product.discount)}%" if product.discount else "0%",

                    "final_price": round(float(product.price) - (float(product.price) * float(product.discount or 0) / 100), 2),
                    "availability": product.availability,
                    "quantity": product.quantity,
                    "cart_status": product.cart_status
                })
        
            response_data = {
                "message": "Products retrieved successfully.",
                "products": product_list,
                "status_code": 200
            }

            if customer_id:
                response_data["customer_id"] = str(customer_id)
            return JsonResponse(response_data, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data.", "status_code": 400}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"An unexpected error occurred: {str(e)}", "status_code": 500}, status=500)

    return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)

# @csrf_exempt
# def customer_search_products(request):
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#             customer_id = data.get('customer_id')
#             category_id = data.get('category_id')
#             sub_category_id = data.get('sub_category_id')
#             product_name = data.get('product_name', '').strip()  # Optional search term

#             if not category_id:
#                 return JsonResponse({"error": "Category ID are required.", "status_code": 400}, status=400)
#             if not sub_category_id:
#                 return JsonResponse({"error": "Sub Category ID are required.", "status_code": 400}, status=400)

#             if product_name == "":
#                 return JsonResponse({"error": "Atleast one character is required.", "status_code": 400}, status=400)

#             products = ProductsDetails.objects.filter(
                
#                 category_id=category_id,
#                 sub_category_id=sub_category_id,
#                 product_status=1
#             )
#             if product_name:
#                 products = products.filter(product_name__icontains=product_name)


#             if not products.exists():
#                 response_data = {"message": "No products details found", "status_code": 200}
#                 if customer_id:
#                     response_data["customer_id"] = customer_id  # Include customer_id if available
#                 return JsonResponse(response_data, status=200)    

#             product_list = []
#             for product in products:
#                 product_images = product.product_images
#                 if isinstance(product_images, list):
#                     product_image_url = (
#                         f"/static/images/products/{os.path.basename(product_images[0].replace('\\', '/'))}"
#                         if product_images else ""
#                     )
#                 elif isinstance(product_images, str):
#                     product_image_url = f"/static/images/products/{os.path.basename(product_images.replace('\\', '/'))}"
#                 else:
#                     product_image_url = ""      

#                 product_list.append({
#                     "product_id": str(product.id),
#                     "product_name": product.product_name,
#                     "category_id": str(product.category_id),
#                     "sub_category_id": str(product.sub_category_id),
#                     "product_image_url": product_image_url,
#                 })
        
#             response_data = {
#                 "message": "Products retrieved successfully.",
#                 "categories": product_list,
#                 "status_code": 200
#             }

#             if customer_id:
#                 response_data["customer_id"] = str(customer_id)
#             return JsonResponse(response_data, status=200)

#         except json.JSONDecodeError:
#             return JsonResponse({"error": "Invalid JSON data.", "status_code": 400}, status=400)
#         except Exception as e:
#             return JsonResponse({"error": f"An unexpected error occurred: {str(e)}", "status_code": 500}, status=500)

#     return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)

#order admin
@csrf_exempt
def get_payment_details_by_order(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
        admin_id = data.get('admin_id')
       
        if not admin_id:
                return JsonResponse({"error": "admin_id is required.", "status_code": 400}, status=400)
     
        payments = PaymentDetails.objects.filter(admin_id=admin_id).order_by('-created_at')
        if not payments.exists():
            return JsonResponse({"error": "No payment details found on this admin.", "status_code": 404}, status=404)

        payment_list = []
        for payment in payments:
            order_ids = payment.order_product_ids  # Assuming this is a list
            
            order_products = OrderProducts.objects.filter(id__in=order_ids)
            
            order_product_list = []
            for order in order_products:
                product = ProductsDetails.objects.filter(id=order.product_id).first()
                # product_image = product.product_images[0] if product and product.product_images else ""
                if product and product.product_images:
                   product_image_path = product.product_images[0].replace('\\', '/')
                   product_image_url = f"{settings.AWS_S3_BUCKET_URL}/{product_image_path}"

                else:
                   product_image_url = ""
                
                order_product_list.append({
                    "id": order.id,
                    "quantity": order.quantity,
                    "price": order.price,
                    # "discount":product.discount,
                    # "final_price": order.final_price,
                    "gst": f"{int(product.gst or 0)}%",
                    "discount":f"{int(product.discount)}%" if product.discount else "0%",
                    "final_price": "{:.2f}".format(float(product.price) - (float(product.price) * float(product.discount or 0) / 100)),
                    "order_status": order.order_status,
                    "product_id": order.product_id,
                    "product_image": product_image_url,
                    "product_name":product.product_name,
                    "shipping_status":order.shipping_status,
                    "delivery_status":order.delivery_status
                    
                })
            # customer_data=[]
            # if payment.customer_id:
            #     customer_obj = CustomerRegisterDetails.objects.filter(id=payment.customer_id).first()
            #     if customer_obj:
            #         customer_data.append({
            #             "customer_id":customer_obj.id,
            #             "customer_name": f"{customer_obj.first_name} {customer_obj.last_name}",
            #             "email":customer_obj.email,
            #             "mobile_no":customer_obj.mobile_no,
            #         })

            address_data = []
            if payment.customer_address_id:
                address_obj = CustomerAddress.objects.filter(id=payment.customer_address_id).first()
                if address_obj:
                    address_data.append({
                        "address_id": address_obj.id,
                        "customer_name": f"{address_obj.first_name} {address_obj.last_name}",
                        "email": address_obj.email,
                        "mobile_number": address_obj.mobile_number,
                        "alternate_mobile": address_obj.alternate_mobile,
                        "address_type": address_obj.address_type,
                        "pincode": address_obj.pincode,
                        "street": address_obj.street,
                        "landmark": address_obj.landmark,
                        "village": address_obj.village,
                        "mandal": address_obj.mandal,
                        "postoffice": address_obj.postoffice,
                        "district": address_obj.district,
                        "state": address_obj.state,
                        "country": address_obj.country,
                        
                    })
                    
                    # address_dict = model_to_dict(address_obj)

            payment_list.append({
                "razorpay_order_id": payment.razorpay_order_id,
                "customer_name": f"{payment.customer.first_name} {payment.customer.last_name}",
                "customer_id":payment.customer_id,
                # "first_name": payment.customer.first_name,
                # "last_name": payment.customer.last_name,
                "email": payment.customer.email,
                "mobile_number": payment.customer.mobile_no,
                "payment_mode": payment.payment_mode,
                "total_quantity":payment.quantity,
                "total_amount": payment.total_amount,
                "payment_date": payment.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "product_order_id":payment.product_order_id,
                "customer_address": address_data,
                "order_products": order_product_list
            })
        response_data = {
            "message": "Placed Order retrieved successfully.",
            "payments": payment_list,
            "status_code": 200
        }

        if admin_id:
            response_data["admin_id"] = str(admin_id)
        return JsonResponse(response_data, status=200)

        # return JsonResponse({"payments": payment_list, "status_code": 200}, status=200)
    
    except Exception as e:
        return JsonResponse({"error": str(e), "status_code": 500}, status=500)

@csrf_exempt
def filter_my_order(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
        customer_id = data.get('customer_id')
        delivery_status_filter = data.get('delivery_status')
        shipping_status_filter = data.get('shipping_status')  # new
        delivery_status_filter = data.get('delivery_status')
        shipping_status_filter = data.get('shipping_status')  # new
        order_time_filter = data.get('order_time')

        if shipping_status_filter and delivery_status_filter:
            return JsonResponse({
                "error": "Please provide only one of 'shipping_status' or 'delivery_status', not both.",
                "status_code": 400
            }, status=400)

        if not customer_id:
            return JsonResponse({"error": "customer_id is required.", "status_code": 400}, status=400)

        payments = PaymentDetails.objects.filter(customer_id=customer_id)

        available_years = payments.dates('created_at', 'year', order='DESC')
        year_options = ["Last 30 days"] + [dt.year for dt in available_years if dt.year >= datetime.now().year - 3] + ["Older"]

        now = datetime.now()
        if order_time_filter:
            if order_time_filter == "Last 30 days":
                payments = payments.filter(created_at__gte=now - timedelta(days=30))
            elif order_time_filter == "Older":
                payments = payments.filter(created_at__lt=datetime(now.year - 3, 1, 1))
            elif order_time_filter.isdigit():
                payments = payments.filter(created_at__year=int(order_time_filter))

        payments = payments.order_by('-created_at')

        if not payments.exists():
            return JsonResponse({"error": "No order details found.", "status_code": 404}, status=404)

        payment_list = []
        total_matched_order_products = 0

        for payment in payments:
            order_ids = payment.order_product_ids
            order_products = OrderProducts.objects.filter(id__in=order_ids)

            # Apply delivery_status or shipping_status filters
            if delivery_status_filter:
                order_products = order_products.filter(delivery_status=delivery_status_filter)
            elif shipping_status_filter == "Shipped":
                order_products = order_products.filter(
                    shipping_status="Shipped"
                ).exclude(delivery_status="Delivered")

            order_product_list = []
            for order in order_products:
                product = ProductsDetails.objects.filter(id=order.product_id).first()
                if product and product.product_images:
                    product_image_path = product.product_images[0].replace('\\', '/')
                    product_image_url = f"{settings.AWS_S3_BUCKET_URL}/{product_image_path.lstrip('/')}"
                else:
                    product_image_url = ""
                # product_image = product.product_images[0] if product and product.product_images else ""

                order_product_list.append({
                    "order_product_id": order.id,
                    "quantity": order.quantity,
                    "price": order.price,
                    "discount": f"{int(product.discount)}%" if product.discount else "0%",
                    "final_price": round(float(product.price) - (float(product.price) * float(product.discount or 0) / 100), 2),
                    "order_status": order.order_status,
                    "shipping_status": order.shipping_status,
                    "delivery_status": order.delivery_status,
                    "product_id": order.product_id,
                    "product_image": product_image_url,
                    "product_name": product.product_name
                })

            if order_product_list:
                total_matched_order_products += len(order_product_list)
            else:
                if delivery_status_filter or shipping_status_filter:
                    continue

            address_data = []
            if payment.customer_address_id:
                address_obj = CustomerAddress.objects.filter(id=payment.customer_address_id).first()
                if address_obj:
                    address_data.append({
                        "address_id": address_obj.id,
                        "customer_name": f"{address_obj.first_name} {address_obj.last_name}",
                        "email": address_obj.email,
                        "mobile_number": address_obj.mobile_number,
                        "alternate_mobile": address_obj.alternate_mobile,
                        "address_type": address_obj.address_type,
                        "pincode": address_obj.pincode,
                        "street": address_obj.street,
                        "landmark": address_obj.landmark,
                        "village": address_obj.village,
                        "mandal": address_obj.mandal,
                        "postoffice": address_obj.postoffice,
                        "district": address_obj.district,
                        "state": address_obj.state,
                        "country": address_obj.country,
                    })

            payment_list.append({
                "customer_name": f"{payment.customer.first_name} {payment.customer.last_name}",
                "email": payment.customer.email,
                "mobile_number": payment.customer.mobile_no,
                "payment_mode": payment.payment_mode,
                "total_quantity": payment.quantity,
                "total_amount": payment.total_amount,
                "payment_date": payment.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "time_filters": year_options,
                "product_order_id": payment.product_order_id,
                "customer_address": address_data,
                "order_products": order_product_list
            })

        if (delivery_status_filter or shipping_status_filter) and total_matched_order_products == 0:
            return JsonResponse({
                "error": "No products found for the selected filters.",
                "status_code": 404,
                "time_filters": year_options
            }, status=404)

        if not payment_list:
            return JsonResponse({"error": "No order details match filters.", "status_code": 404}, status=404)

        return JsonResponse({
            "message": "Filtered Orders Retrieved Successfully.",
            "payments": payment_list,
            "status_code": 200,
            "customer_id": str(customer_id)
        }, status=200)

    except Exception as e:
        return JsonResponse({"error": str(e), "status_code": 500}, status=500)

@csrf_exempt
def customer_get_payment_details_by_order(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
        customer_id = data.get('customer_id')
       
        if not customer_id:
                return JsonResponse({"error": "customer_id is required.", "status_code": 400}, status=400)
     
        # payments = PaymentDetails.objects.filter(customer_id=customer_id)
        payments = PaymentDetails.objects.filter(customer_id=customer_id).order_by('-created_at')

        if not payments.exists():
            return JsonResponse({"error": "No order details found.", "status_code": 404}, status=404)

        payment_list = []
        for payment in payments:
            order_ids = payment.order_product_ids  # Assuming this is a list
            
            order_products = OrderProducts.objects.filter(id__in=order_ids)
            
            order_product_list = []
            for order in order_products:
                product = ProductsDetails.objects.filter(id=order.product_id).first()
                if product and product.product_images:
                     product_image_path = product.product_images[0].replace('\\', '/')
                     product_image_url = f"{settings.AWS_S3_BUCKET_URL}/{product_image_path.lstrip('/')}"
                else:
                     product_image_url = ""
                
                order_product_list.append({
                    "order_product_id": order.id,
                    "quantity": order.quantity,
                    "price": order.price,
                    # "discount":product.discount,
                    # "final_price": order.final_price,
                    "gst": f"{int(product.gst or 0)}%",
                    "discount":f"{int(product.discount)}%" if product.discount else "0%",
                    "final_price": round(float(product.price) - (float(product.price) * float(product.discount or 0) / 100), 2),
                    "order_status": order.order_status,
                    "shipping_status":order.shipping_status,
                    "delivery_status":order.delivery_status,
                    "product_id": order.product_id,
                    "product_image": product_image_url,
                    "product_name":product.product_name
                })
          
            address_data = []
            if payment.customer_address_id:
                address_obj = CustomerAddress.objects.filter(id=payment.customer_address_id).first()
                if address_obj:
                    address_data.append({
                        
                        "address_id": address_obj.id,
                        "customer_name": f"{address_obj.first_name} {address_obj.last_name}",
                        "email": address_obj.email,
                        "mobile_number": address_obj.mobile_number,
                        "alternate_mobile": address_obj.alternate_mobile,
                        "address_type": address_obj.address_type,
                        "pincode": address_obj.pincode,
                        "street": address_obj.street,
                        "landmark": address_obj.landmark,
                        "village": address_obj.village,
                        "mandal": address_obj.mandal,
                        "postoffice": address_obj.postoffice,
                        "district": address_obj.district,
                        "state": address_obj.state,
                        "country": address_obj.country,
                        
                    })
                    
            payment_list.append({
                "razorpay_order_id": payment.razorpay_order_id,
                "customer_name": f"{payment.customer.first_name} {payment.customer.last_name}",
                "email": payment.customer.email,
                "mobile_number": payment.customer.mobile_no,
                "payment_mode": payment.payment_mode,
                "total_quantity":payment.quantity,
                "price":order.price,
                "total_amount": payment.total_amount,
                "payment_date": payment.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "product_order_id":payment.product_order_id,
                "customer_address": address_data,
                "order_products": order_product_list
            })
        response_data = {
            "message": "Placed Order retrieved successfully.",
            "payments": payment_list,
            "status_code": 200
        }

        if customer_id:
            response_data["customer_id"] = str(customer_id)
        return JsonResponse(response_data, status=200)    
    except Exception as e:
        return JsonResponse({"error": str(e), "status_code": 500}, status=500)    


import boto3
from botocore.exceptions import ClientError
def download_material_file(request, product_id):
    try:
        # Fetch product from the database
        product = ProductsDetails.objects.get(id=product_id)
        material_key = product.material_file  # Path stored in the database

        if not material_key:
            return JsonResponse({"error": "Material file not found.", "status_code": 404}, status=404)
        
        s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )

        try:
            # Get the file from S3
            file_obj = s3.get_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=material_key)
            file_content = file_obj['Body'].read()

            # Return the file as a response
            response = FileResponse(file_content, as_attachment=True)
            response['Content-Disposition'] = f'attachment; filename="{material_key.replace("\\", "/").split("/")[-1]}"'

            response['Content-Type'] = file_obj['ContentType']  # Adjust the MIME type if necessary

            return response

        except ClientError as e:
            return JsonResponse({"error": f"Failed to fetch material file from S3: {str(e)}", "status_code": 500}, status=500)


    except ProductsDetails.DoesNotExist:
        return JsonResponse({"error": "Product not found.", "status_code": 404}, status=404)
    except Exception as e:
        return JsonResponse({"error": f"Unexpected error: {str(e)}", "status_code": 500}, status=500)


@csrf_exempt
def get_customer_profile(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            customer_id = data.get("customer_id")

            if not customer_id:
                return JsonResponse({"error": "Customer ID is required.", "status_code": 400}, status=400)

            try:
                customer = CustomerRegisterDetails.objects.get(id=customer_id)
            except CustomerRegisterDetails.DoesNotExist:
                return JsonResponse({"error": "Customer not found.", "status_code": 404}, status=404)

            return JsonResponse({
                "message": "Customer profile fetched successfully.",
                "status_code": 200,
                "customer_id": customer.id,
                "profile": {
                    "first_name": customer.first_name,
                    "last_name": customer.last_name,
                    "email": customer.email,
                    "mobile_no": customer.mobile_no,
                }
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format.", "status_code": 400}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"An unexpected error occurred: {str(e)}", "status_code": 500}, status=500)

    return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)


@csrf_exempt
def edit_customer_profile(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            customer_id = data.get("customer_id")

            
            if not customer_id:
                return JsonResponse({"error": "Customer ID is required.", "status_code": 400}, status=400)

       
            try:
                customer = CustomerRegisterDetails.objects.get(id=customer_id)
            except CustomerRegisterDetails.DoesNotExist:
                return JsonResponse({"error": "Customer not found.", "status_code": 404}, status=404)

            
            customer.first_name = data.get("first_name", customer.first_name)
            customer.last_name = data.get("last_name", customer.last_name)
            # customer.email = data.get("email", customer.email)
            # customer.mobile_no = data.get("mobile_no", customer.mobile_no)

            customer.save(update_fields=["first_name", "last_name"])

            return JsonResponse({
                "message": "Customer profile updated successfully.",
                "status_code": 200,
                "customer_id": customer.id,
                "updated_details": {
                    "first_name": customer.first_name,
                    "last_name": customer.last_name,
                    # "email": customer.email,
                    # "mobile_no": customer.mobile_no,
                }
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format.", "status_code": 400}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"An unexpected error occurred: {str(e)}", "status_code": 500}, status=500)

    return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)

from django.utils.timezone import now
from django.db.models import Sum


@csrf_exempt
def report_sales_summary(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
        admin_id = data.get('admin_id')

        if not admin_id:
            return JsonResponse({"error": "admin_id is required.", "status_code": 400}, status=400)

        today = now().date()
        this_month = today.month
        this_year = today.year

        todays_sales = PaymentDetails.objects.filter(admin_id=admin_id, created_at__date=today)
        month_sales = PaymentDetails.objects.filter(admin_id=admin_id, created_at__month=this_month, created_at__year=this_year)
        total_sales = PaymentDetails.objects.filter(admin_id=admin_id,created_at__year=this_year)

        todays_amount = todays_sales.aggregate(total=Sum('total_amount'))['total'] or 0
        month_amount = month_sales.aggregate(total=Sum('total_amount'))['total'] or 0
        total_amount = total_sales.aggregate(total=Sum('total_amount'))['total'] or 0

        return JsonResponse({
            "today_sales_amount": todays_amount,
            "this_month_sales_amount": month_amount,
            "total_sales_amount": total_amount,
            "status_code": 200,
            "admin_id":admin_id
        }, status=200)

    except Exception as e:
        return JsonResponse({"error": str(e), "status_code": 500}, status=500)

# import calendar
# from dateutil.relativedelta import relativedelta

# @csrf_exempt
# def report_monthly_revenue_by_year(request):
#     if request.method != "POST":
#         return JsonResponse({"error": "Only POST method allowed", "status_code": 405}, status=405)

#     try:
#         data = json.loads(request.body.decode("utf-8"))
#         admin_id = data.get('admin_id')
#         start_date_str = data.get('start_date_str')  # e.g., "2024-05-06"
#         end_date_str = data.get('end_date_str')      # e.g., "2025-05-06"

#         # If no start_date_str and end_date_str are provided, use the current year as default
#         if not start_date_str or not end_date_str:
#             current_year = datetime.now().year
#             start_date_str = f"{current_year}-01-01"  # Start of the current year
#             end_date_str = f"{current_year}-12-31"    # End of the current year

#         if not admin_id:
#             return JsonResponse({"error": "admin_id is required", "status_code": 400}, status=400)

#         # Parse start_date and end_date
#         try:
#             start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
#             end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
#         except ValueError:
#             return JsonResponse({"error": "Invalid date format. Use YYYY-MM-DD.", "status_code": 400}, status=400)

#         # Validate the date range (end_date should be after start_date)
#         if end_date < start_date:
#             return JsonResponse({"error": "End date must be after start date", "status_code": 400}, status=400)

#         # Check if start and end date span multiple years
#         if start_date.year != end_date.year:
#             # If the start date is in one year and the end date is in the next, show the error message
#             if start_date.month < end_date.month:  
#                 return JsonResponse({"error": "Please choose a date range within the same year", "status_code": 400}, status=400)

#         # Get the months within the range
#         monthly_revenue = {}
#         current = start_date

#         # Loop over the months within the date range
#         while current <= end_date:
#             key = f"{calendar.month_abbr[current.month]} {current.year}"
#             monthly_revenue[key] = 0  # Initialize the month with 0 revenue
#             current += relativedelta(months=1)  # Move to the next month

#         # Filter payments within the given date range
#         payments = PaymentDetails.objects.filter(
#             admin_id=admin_id,
#             created_at__date__gte=start_date.date(),
#             created_at__date__lte=end_date.date()
#         )

#         # Calculate monthly revenue
#         for payment in payments:
#             key = f"{calendar.month_abbr[payment.created_at.month]} {payment.created_at.year}"
#             if key in monthly_revenue:
#                 monthly_revenue[key] += float(payment.total_amount)

#         # Create a dummy price scale for the graph's y-axis (in increments of 50,000)
#         dummy_y_axis = [i * 50000 for i in range(1, 11)]  # [50K, 100K, 150K, ..., 500K]

#         return JsonResponse({
#             "start_date": start_date_str,
#             "end_date": end_date_str,
#             "monthly_revenue": monthly_revenue,
#             "status_code": 200,
#             "admin_id": admin_id,
#             "dummy_y_axis": dummy_y_axis  # Adding dummy price scale for the y-axis
#         })

#     except Exception as e:
#         return JsonResponse({"error": str(e), "status_code": 500})

from django.db import models
import calendar
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta

@csrf_exempt
def report_monthly_revenue_by_year(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method allowed", "status_code": 405}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
        admin_id = data.get('admin_id')
        action = data.get('action')  # "month" or "year"

        if not admin_id:
            return JsonResponse({"error": "admin_id is required", "status_code": 400}, status=400)

        if action == "month":
            return _report_monthly(data, admin_id)
        elif action == "year":
            return _report_yearly(admin_id)
        elif action == "week":
            return _report_weekly(data, admin_id)
        else:
            return JsonResponse({"error": "Invalid action. Use 'month' or 'year'.", "status_code": 400}, status=400)

    except Exception as e:
        return JsonResponse({"error": str(e), "status_code": 500})

def _report_yearly(admin_id):
    current_year = datetime.now().year
    yearly_revenue = {}
    start_year = current_year - 11  # 12 years total

    for year in range(start_year, current_year + 1):
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31)
        total = PaymentDetails.objects.filter(
            admin_id=admin_id,
            created_at__date__gte=start_date.date(),
            created_at__date__lte=end_date.date()
        ).aggregate(total_amount=models.Sum('total_amount'))['total_amount'] or 0
        yearly_revenue[str(year)] = float(total)

    dummy_y_axis = [i * 500000 for i in range(1, 11)]  # ₹5L, ₹10L, ..., ₹50L

    return JsonResponse({
        "report_type": "yearly",
        "year_range": [start_year, current_year],
        "yearly_revenue": yearly_revenue,
        "admin_id": admin_id,
        "dummy_y_axis": dummy_y_axis,
        "status_code": 200
    })

def _report_monthly(data, admin_id):
    start_date_str = data.get('start_date_str')
    end_date_str = data.get('end_date_str')

    if not start_date_str or not end_date_str:
        current_year = datetime.now().year
        start_date_str = f"{current_year}-01-01"
        end_date_str = f"{current_year}-12-31"

    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    except ValueError:
        return JsonResponse({"error": "Invalid date format. Use YYYY-MM-DD.", "status_code": 400}, status=400)

    if end_date < start_date:
        return JsonResponse({"error": "End date must be after start date", "status_code": 400}, status=400)

    if start_date.year != end_date.year:
        if start_date.month < end_date.month:
            return JsonResponse({"error": "Please choose a date range within the same year", "status_code": 400}, status=400)

    monthly_revenue = {}
    current = start_date
    while current <= end_date:
        key = f"{calendar.month_abbr[current.month]} {current.year}"
        monthly_revenue[key] = 0
        current += relativedelta(months=1)

    payments = PaymentDetails.objects.filter(
        admin_id=admin_id,
        created_at__date__gte=start_date.date(),
        created_at__date__lte=end_date.date()
    )

    for payment in payments:
        key = f"{calendar.month_abbr[payment.created_at.month]} {payment.created_at.year}"
        if key in monthly_revenue:
            monthly_revenue[key] += float(payment.total_amount)

    dummy_y_axis = [i * 50000 for i in range(1, 11)]

    return JsonResponse({
        "report_type": "monthly",
        "start_date": start_date_str,
        "end_date": end_date_str,
        "monthly_revenue": monthly_revenue,
        "admin_id": admin_id,
        "dummy_y_axis": dummy_y_axis,
        "status_code": 200
    })

def _report_weekly(data, admin_id):
# def _report_daywise_by_week(data, admin_id):
    start_date_str = data.get('start_date_str')
    end_date_str = data.get('end_date_str')

    # Default to last 7 days (today inclusive)
    if not start_date_str or not end_date_str:
        end_date = datetime.now().date()
        start_date = end_date - relativedelta(days=6)
    else:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            return JsonResponse({"error": "Invalid date format. Use YYYY-MM-DD.", "status_code": 400}, status=400)

    # Validate 7-day range max
    delta_days = (end_date - start_date).days
    if delta_days < 0:
        return JsonResponse({"error": "End date must be after start date", "status_code": 400}, status=400)
    if delta_days > 6:
        return JsonResponse({"error": "Only 7-day range allowed", "status_code": 400}, status=400)

    # Initialize dictionary with day name + date
    daywise_revenue = {}
    for i in range(delta_days + 1):
        date = start_date + relativedelta(days=i)
        label = f"{date.strftime('%A')} ({date.strftime('%d %b %Y')})"  # Example: "Wednesday (30 Apr 2025)"
        daywise_revenue[label] = 0

    # Get all relevant payments
    payments = PaymentDetails.objects.filter(
        admin_id=admin_id,
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    )

    # Accumulate revenue per day
    for payment in payments:
        pay_date = payment.created_at.date()
        label = f"{pay_date.strftime('%A')} ({pay_date.strftime('%d %b %Y')})"
        if label in daywise_revenue:
            daywise_revenue[label] += float(payment.total_amount)

    dummy_y_axis = [i * 10000 for i in range(1, 11)]  # ₹10K to ₹100K

    return JsonResponse({
        "report_type": "daywise_week",
        "start_date": str(start_date),
        "end_date": str(end_date),
        "daywise_revenue": daywise_revenue,
        "admin_id": admin_id,
        "dummy_y_axis": dummy_y_axis,
        "status_code": 200
    })

from collections import Counter

@csrf_exempt
def top_five_selling_products(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method allowed", "status_code": 405}, status=405)

    try:
        data = json.loads(request.body)
        admin_id = data.get("admin_id")

        if not admin_id:
            return JsonResponse({"error": "admin_id is required", "status_code": 400}, status=400)

        product_counter = Counter()

        # Get all PaymentDetails for the admin
        payments = PaymentDetails.objects.filter(admin_id=admin_id)

        for payment in payments:
            product_ids = payment.product_ids  # Assumes this is a list of product IDs
            product_counter.update(product_ids)

        # Get top 5 most common product IDs
        top_5 = product_counter.most_common(5)
        top_product_ids = [pid for pid, _ in top_5]

        # Corrected field name: use 'id' instead of 'product_id'
        order_products = ProductsDetails.objects.filter(id__in=top_product_ids).values('id', 'product_name')
        product_name_map = {item['id']: item['product_name'] for item in order_products}

        response_data = []
        for pid, count in top_5:
            response_data.append({
                "product_id": pid,
                "product_name": product_name_map.get(pid, "Unknown"),
                "total_sold": count
            })

        return JsonResponse({
            "status_code": 200,
            "top_5_products": response_data
        })

    except Exception as e:
        return JsonResponse({"error": str(e), "status_code": 500})


@csrf_exempt
def not_selling_products(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method allowed", "status_code": 405}, status=405)

    try:
        data = json.loads(request.body)
        admin_id = data.get("admin_id")

        if not admin_id:
            return JsonResponse({"error": "admin_id is required", "status_code": 400}, status=400)

        # Get sold product IDs
        sold_product_ids = []
        payments = PaymentDetails.objects.filter(admin_id=admin_id)
        for payment in payments:
            sold_product_ids.extend(payment.product_ids)  # Assuming it's a list of IDs

        # Get all product IDs
        all_products = ProductsDetails.objects.filter(admin_id=admin_id)
        not_sold_products = all_products.exclude(id__in=sold_product_ids).values('id', 'product_name')

        response_data = list(not_sold_products)

        return JsonResponse({
            "status_code": 200,
            "not_selling_products": response_data
        })

    except Exception as e:
        return JsonResponse({"error": str(e), "status_code": 500})


@csrf_exempt
def get_all_category_subcategory(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
        customer_id = data.get('customer_id')

        categories = CategoryDetails.objects.filter(category_status=1)

        if not categories.exists():
            return JsonResponse({"error": "No categories found.", "status_code": 404}, status=404)

        category_list = []
        for category in categories:

            subcategories = SubCategoryDetails.objects.filter(category=category,sub_category_status=1)            
            sub_category_list = []
            for subcategory in subcategories:
              sub_category_image_url = ""
              if subcategory.sub_category_image:
                    sub_category_image_path = subcategory.sub_category_image.replace('\\', '/')
                    sub_category_image_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{sub_category_image_path}"



              sub_category_list.append({
                    "id": subcategory.id,
                    "sub_category_name": subcategory.sub_category_name,
                    "sub_category_image": sub_category_image_url,
                    
                })     
            category_list.append({
                "category_id":category.id,
                "category_name":category.category_name,  
                "sub_categoryies": sub_category_list
            })
        response_data = {
            "message": "Category and subcategory retrieved successfully.",
            "categories": category_list,
            "status_code": 200
        }

        if customer_id:
            response_data["customer_id"] = str(customer_id)
        return JsonResponse(response_data, status=200)    
    except Exception as e:
        return JsonResponse({"error": str(e), "status_code": 500}, status=500)


@csrf_exempt
def generate_invoice_for_customer(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
        customer_id = data.get("customer_id")
        product_order_id = data.get("product_order_id")
        

        if not customer_id:
            return JsonResponse({"error": "customer_id is required", "status_code": 400}, status=400)

        payments = PaymentDetails.objects.filter(customer_id=customer_id,product_order_id=product_order_id)

        if not payments.exists():
            return JsonResponse({"error": "No invoices found for this customer", "status_code": 404}, status=404)

        invoice_list = []
        for payment in payments:
            # Generate custom invoice number
            # today = payment.created_at.date()
            # date_str = today.strftime("%d%m%Y")  # e.g., 18042025
            # prefix = "PVM"
            # base_invoice = f"{prefix}{date_str}"

            # # Fetch latest invoice number with this prefix
            # latest_invoice = PaymentDetails.objects.filter(
            #     created_at__date=today
            # ).exclude(id=payment.id).order_by('-id').first()

            # if latest_invoice and hasattr(latest_invoice, 'custom_invoice_no'):
            #     last_serial = int(latest_invoice.custom_invoice_no[-4:])
            # else:
            #     last_serial = 0

            # new_serial = last_serial + 1
            # new_invoice_number = f"{base_invoice}{str(new_serial).zfill(4)}"  # 0001 format

            # # Save the new invoice number to the payment (optional)
            # # payment.custom_invoice_no = new_invoice_number
            # # payment.save()

      
            order_ids = payment.order_product_ids
            order_products = OrderProducts.objects.filter(id__in=order_ids)
            customer=CustomerRegisterDetails.objects.filter(id=payment.customer_id).first()
            address = CustomerAddress.objects.filter(id=payment.customer_address_id).first()

            items = []
            for order in order_products:
                product = ProductsDetails.objects.filter(id=order.product_id).first()
                if not product:
                    continue
                # GST calculation based on 5% rate
                # base_price = round(order.final_price / Decimal("1.05"), 2)
                # # base_price = round(order.final_price / 1.05, 2)
                # gst_amount = round(order.final_price - base_price, 2)
                price = float(product.price)
                discount_percent = float(product.discount or 0)

                discount_amount = (price * discount_percent) / 100
                final_price = price - discount_amount
                base_price = round(order.final_price / Decimal("1.05"), 2)
                gst_amount = round(order.final_price - base_price, 2)

                items.append({
                    "product_name": product.product_name,
                    "sku":product.sku_number,
                    "quantity": order.quantity,
                    "price" :product.price,
                    "gst": f"{int(product.gst or 0)}%",
                    "discount_percent": f"{int(discount_percent)}%",
                    "discount": round(discount_amount, 2),
                    # "discount": product.discount,
                    # "gross_amount": order.final_price,
                    # "discount":float(0.00),
                    
                    "gross_amount": round(final_price),
                    "taxable_value": base_price,
                    "igst": gst_amount,
                    "total": order.final_price,
                })

            invoice_list.append({
                # "invoice_number": f"INV-{payment.id}",
                "invoice_number":payment.invoice_number,
                "order_id": payment.product_order_id,
                "order_date": payment.created_at.strftime("%d-%m-%Y"),
                "invoice_date": payment.invoice_date.strftime("%d-%m-%Y"),
                "Billing To": {
                    "name": f"{customer.first_name} {customer.last_name}" if customer else "",
                    # "address": f"{customer.street}, {customer.landmark}, {customer.village}, {customer.district}, {customer.state}, {customer.pincode}" if customer else "",
                    "phone": customer.mobile_no if customer else "",
                },
                "Delivery To": {
                    "name": f"{address.first_name} {address.last_name}" if address else "",
                    "address": f"{address.street}, {address.landmark}, {address.village}, {address.district}, {address.state}, {address.pincode}" if address else "",
                    "phone": address.mobile_number if address else "",
                },
                "sold_by": "Pavaman",
                "gstin": "XXABCDEFGH1Z1",
                "total_items": len(items),
                "items": items,
                "grand_total": payment.total_amount,
                "payment_mode": payment.payment_mode,
                "gst_rate": "5%",
            })

        return JsonResponse({
            "message": "Invoice(s) generated successfully",
            "invoices": invoice_list,
            "status_code": 200
        }, status=200)

    except Exception as e:
        return JsonResponse({"error": str(e), "status_code": 500}, status=500)

#pie chart order status
@csrf_exempt
def admin_order_status(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        admin_id = data.get("admin_id")

        if not admin_id:
            return JsonResponse({"error": "admin_id is required.", "status_code": 400}, status=400)

        # Step 1: Fetch all PaymentDetails by this admin
        payment_entries = PaymentDetails.objects.filter(admin_id=admin_id)

        if not payment_entries.exists():
            return JsonResponse({
                "error": "No payment records found for this admin.",
                "status_code": 404
            }, status=404)

        # Step 2: Collect all order_product_ids from these entries
        all_order_product_ids = []
        for entry in payment_entries:
            if isinstance(entry.order_product_ids, list):
                all_order_product_ids.extend(entry.order_product_ids)

        if not all_order_product_ids:
            return JsonResponse({
                "error": "No order_product_ids found in PaymentDetails for this admin.",
                "status_code": 404
            }, status=404)

        all_order_product_ids = list(set(all_order_product_ids))  # Deduplicate

        # Step 3: Get all OrderProducts that match these order_product_ids
        related_orders = OrderProducts.objects.filter(id__in=all_order_product_ids)

        # Step 4: Count order statuses using Counter for 'Paid' and 'Cancelled'
        status_counter = Counter(order.order_status for order in related_orders)

        # Step 5: Count pending orders from
        #  the entire OrderProducts table (no filter based on order_product_ids)
        pending_orders = OrderProducts.objects.filter(order_status="Pending").count()

        # Prepare the result
        result = {
            "Paid": status_counter.get("Paid", 0),
            "Pending": pending_orders,
            "Cancelled": status_counter.get("Cancelled", 0),
        }

        return JsonResponse({
            "admin_id": admin_id,
            "total_related_orders": related_orders.count(),
            "order_status_summary": result,
            "status_code": 200
        }, status=200)

    except Exception as e:
        return JsonResponse({"error": str(e), "status_code": 500}, status=500)
@csrf_exempt
def customer_cart_view_search(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            customer_id = data.get('customer_id')
            product_name = data.get('product_name', '').strip()

            if not customer_id:
                return JsonResponse({"error": "Customer ID is required.", "status_code": 400}, status=400)

            cart_items = CartProducts.objects.filter(customer_id=customer_id)

            if product_name:
                cart_items = cart_items.filter(product__product_name__icontains=product_name)

            if not cart_items.exists():
                return JsonResponse({
                    "message": "No cart items found.",
                    "status_code": 200,
                    "customer_id": str(customer_id)
                }, status=200)

            cart_list = []
            for item in cart_items:
                product = item.product

                # Calculate totals
                # price = float(product.price)
                # discount = float(product.discount or 0)
                # discount_price = price - discount
                # item_total_price = discount_price * item.quantity

                price = float(product.price)
                discount= float(product.discount or 0)  
                discount_amount = (price * discount) / 100  
                final_price = price - discount_amount  
                total_price = final_price * item.quantity 
                product_image_url = ""
                if product.product_images:
                    product_image_path = product.product_images[0].replace('\\', '/')
                    product_image_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{product_image_path}"

 


                cart_list.append({
                    "cart_id": item.id,
                    "product_id": product.id,
                    "product_name": product.product_name,
                    "quantity": item.quantity,
                    "price": price,
                    "gst": f"{int(product.gst or 0)}%",
                    "discount": f"{int(discount)}%",
                    "final_price": round(final_price, 2),
                    "total_price": round(total_price, 2),
                    "original_quantity": product.quantity,
                    "availability": product.availability,
                    "image": product_image_url,
                    "category": product.category.category_name if product.category else None,
                    "sub_category": product.sub_category.sub_category_name if product.sub_category else None
                })

            return JsonResponse({
                "message": "Cart items retrieved successfully.",
                "cart_items": cart_list,
                "status_code": 200,
                "customer_id": str(customer_id)
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data.", "status_code": 400}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"An unexpected error occurred: {str(e)}", "status_code": 500}, status=500)

    return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)



@csrf_exempt
def edit_profile_mobile_otp_handler(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            action = data.get("action")
            customer_id = data.get("customer_id")

            if not action or not customer_id:
                return JsonResponse({"error": "Action and Customer ID are required.", "customer_id": customer_id}, status=400)

            customer = CustomerRegisterDetails.objects.filter(id=customer_id).first()
            if not customer:
                return JsonResponse({"error": "Customer not found.", "customer_id": customer_id}, status=404)

            if action == "send_previous_otp":
                if not customer.mobile_no:
                    return JsonResponse({"error": "Customer does not have a registered mobile number.", "customer_id": customer_id}, status=400)

                otp = random.randint(100000, 999999)
                customer.otp = otp
                customer.save(update_fields=["otp"])

                message = f"Your OTP for verifying your current mobile number is: {otp}"
                send_bulk_sms([customer.mobile_no], message)

                return JsonResponse({
                    "message": "OTP sent to previous mobile number.",
                    "customer_id": customer_id
                })

            elif action == "verify_previous_otp":
                otp = data.get("otp")
                if not otp:
                    return JsonResponse({"error": "OTP is required for verification.", "customer_id": customer_id}, status=400)

                if str(customer.otp) != str(otp):
                    return JsonResponse({"error": "Invalid OTP for previous mobile number.", "customer_id": customer_id}, status=400)

                customer.otp = None
                customer.save(update_fields=["otp"])

                return JsonResponse({
                    "message": "Previous mobile verified.",
                    "customer_id": customer_id,
                    "previous_mobile": customer.mobile_no
                })

            elif action == "send_new_otp":
                new_mobile = data.get("mobile_no")
                if not new_mobile:
                    return JsonResponse({"error": "New mobile number is required.", "customer_id": customer_id}, status=400)

                otp = random.randint(100000, 999999)
                customer.otp = otp
                customer.mobile_no = new_mobile
                customer.save(update_fields=["otp", "mobile_no"])

                message = f"Your OTP for verifying your new mobile number is: {otp}"
                send_bulk_sms([new_mobile], message)

                return JsonResponse({
                    "message": "OTP sent to new mobile number.",
                    "customer_id": customer_id,
                    "new_mobile": new_mobile
                })

            elif action == "verify_new_otp":
                otp = data.get("otp")
                if not otp:
                    return JsonResponse({"error": "OTP is required for verification.", "customer_id": customer_id}, status=400)

                if str(customer.otp) != str(otp):
                    return JsonResponse({"error": "Invalid OTP for new mobile number.", "customer_id": customer_id}, status=400)

                customer.otp = None
                customer.save(update_fields=["otp"])

                return JsonResponse({
                    "message": "New mobile number verified successfully.",
                    "customer_id": customer_id,
                    "new_mobile": customer.mobile_no
                })

            else:
                return JsonResponse({"error": "Invalid action type.", "customer_id": customer_id}, status=400)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format."}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"Server error: {str(e)}", "customer_id": customer_id}, status=500)

    return JsonResponse({"error": "Invalid request method."}, status=405)





@csrf_exempt
def edit_profile_email_otp_handler(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            action = data.get("action")
            customer_id = data.get("customer_id")

            if not action or not customer_id:
                return JsonResponse({"error": "Action and Customer ID are required.", "customer_id": customer_id}, status=400)

            customer = CustomerRegisterDetails.objects.filter(id=customer_id).first()
            if not customer:
                return JsonResponse({"error": "Customer not found.", "customer_id": customer_id}, status=404)

            if action == "send_previous_otp":
                if not customer.email:
                    return JsonResponse({"error": "Customer does not have a registered email address.", "customer_id": customer_id}, status=400)

                otp = random.randint(100000, 999999)
                customer.otp = otp
                customer.otp_send_type = 'email'
                customer.save(update_fields=["otp", "otp_send_type"])

                subject = "Verify Your Email"
                message = f"Your OTP for verifying your current email is: {otp}"
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [customer.email])

                return JsonResponse({
                    "message": "OTP sent to previous email address.",
                    "customer_id": customer_id
                })

            elif action == "verify_previous_otp":
                otp = data.get("otp")
                if not otp:
                    return JsonResponse({"error": "OTP is required for verification.", "customer_id": customer_id}, status=400)

                if str(customer.otp) != str(otp):
                    return JsonResponse({"error": "Invalid OTP for previous email.", "customer_id": customer_id}, status=400)

                customer.otp = None
                customer.save(update_fields=["otp"])

                return JsonResponse({
                    "message": "Previous email verified.",
                    "customer_id": customer_id,
                    "previous_email": customer.email
                })

            elif action == "send_new_otp":
                new_email = data.get("email")
                if not new_email:
                    return JsonResponse({"error": "New email address is required.", "customer_id": customer_id}, status=400)

                otp = random.randint(100000, 999999)
                customer.otp = otp
                customer.email = new_email
                customer.otp_send_type = 'email'
                customer.save(update_fields=["otp", "email", "otp_send_type"])

                subject = "Verify Your New Email"
                message = f"Your OTP for verifying your new email address is: {otp}"
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [new_email])

                return JsonResponse({
                    "message": "OTP sent to new email address.",
                    "customer_id": customer_id,
                    "new_email": new_email
                })

            elif action == "verify_new_otp":
                otp = data.get("otp")
                if not otp:
                    return JsonResponse({"error": "OTP is required for verification.", "customer_id": customer_id}, status=400)

                if str(customer.otp) != str(otp):
                    return JsonResponse({"error": "Invalid OTP for new email address.", "customer_id": customer_id}, status=400)

                customer.otp = None
                customer.save(update_fields=["otp"])

                return JsonResponse({
                    "message": "New email address verified successfully.",
                    "customer_id": customer_id,
                    "new_email": customer.email
                })

            else:
                return JsonResponse({"error": "Invalid action type.", "customer_id": customer_id}, status=400)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format."}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"Server error: {str(e)}", "customer_id": customer_id}, status=500)

    return JsonResponse({"error": "Invalid request method."}, status=405)



@csrf_exempt
def filter_and_sort_products(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode('utf-8'))

            category_id = data.get("category_id")
            category_name = data.get("category_name")
            subcategory_id = data.get("sub_category_id")
            sub_category_name = data.get("sub_category_name")
            min_price = data.get("min_price")
            max_price = data.get("max_price")
            sort_by = data.get("sort_by")

            customer_id = data.get("customer_id") or request.session.get('customer_id')

            if not category_id or not category_name:
                return JsonResponse({"error": "category_id and category_name are required.", "status_code": 400}, status=400)

            if not subcategory_id or not sub_category_name:
                return JsonResponse({"error": "sub_category_id and sub_category_name are required.", "status_code": 400}, status=400)

            try:
                category = CategoryDetails.objects.get(id=category_id)
                if category.category_name != category_name:
                    return JsonResponse({"error": "Incorrect category_name for the given category_id.", "status_code": 400}, status=400)
            except CategoryDetails.DoesNotExist:
                return JsonResponse({"error": "Invalid category_id. Category not found.", "status_code": 404}, status=404)

            try:
                subcategory = SubCategoryDetails.objects.get(id=subcategory_id, category_id=category_id, sub_category_status=1)
                if subcategory.sub_category_name != sub_category_name:
                    return JsonResponse({"error": "Incorrect sub_category_name for the given sub_category_id.", "status_code": 400}, status=400)
            except SubCategoryDetails.DoesNotExist:
                return JsonResponse({"error": "Invalid sub_category_id for the given category.", "status_code": 404}, status=404)

            products_query = ProductsDetails.objects.filter(
                category_id=category_id,
                sub_category_id=subcategory_id,
                product_status=1
            )

            if min_price is not None and isinstance(min_price, (int, float)):
                products_query = products_query.filter(price__gte=min_price)

            if max_price is not None and isinstance(max_price, (int, float)):
                products_query = products_query.filter(price__lte=max_price)

            if sort_by == "latest":
                products_query = products_query.order_by("-created_at")
            elif sort_by == "low_to_high":
                products_query = products_query.order_by("price")
            elif sort_by == "high_to_low":
                products_query = products_query.order_by("-price")
            else:
                return JsonResponse({"error": "Invalid sort_by value. Use 'latest', 'low_to_high', or 'high_to_low'.", "status_code": 400}, status=400)

            products_list = []
            for product in products_query:
                product_images_url = []

                # Safely handle product_images whether it's a string or list
                if product.product_images:
                    if isinstance(product.product_images, str):
                        product_images = product.product_images.split(',')
                    elif isinstance(product.product_images, list):
                        product_images = product.product_images
                    else:
                        product_images = []

                    for image in product_images:
                        image_path = image.replace('\\', '/')
                        product_images_url.append(f"{settings.AWS_S3_BUCKET_URL}/{image_path.lstrip('/')}")

                else:
                    product_images_url = []

                product_data = {
                    "product_id": str(product.id),
                    "product_name": product.product_name,
                    "sku_number": product.sku_number,
                    "price": float(product.price),
                    "gst": f"{int(product.gst or 0)}%",
                    "discount": f"{int(product.discount)}%" if product.discount else "0%",
                    "final_price": round(float(product.price) - (float(product.price) * float(product.discount or 0) / 100), 2),
                    "availability": product.availability,
                    "quantity": product.quantity,
                    "description": product.description,
                    "product_images": product_images_url,
                    "material_file": product.material_file,
                    "number_of_specifications": product.number_of_specifications,
                    "specifications": product.specifications,
                }

                products_list.append(product_data)

            price_range = products_query.aggregate(
                min_price=Min("price"),
                max_price=Max("price")
            )

            if price_range["min_price"] is None:
                price_range["min_price"] = min_price if min_price is not None else 0
            if price_range["max_price"] is None:
                price_range["max_price"] = max_price if max_price is not None else 0

            response_data = {
                "message": "Filtered products retrieved successfully.",
                "category_id": category_id,
                "category_name": category.category_name,
                "sub_category_id": subcategory_id,
                "sub_category_name": subcategory.sub_category_name,
                "min_price": price_range["min_price"],
                "max_price": price_range["max_price"],
                "products": products_list,
                "status_code": 200,
            }

            if customer_id:
                response_data["customer_id"] = customer_id

            return JsonResponse(response_data, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format.", "status_code": 400}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"Server error: {str(e)}", "status_code": 500}, status=500)

    return JsonResponse({"error": "Invalid request method. Use POST.", "status_code": 405}, status=405)




@csrf_exempt
def submit_feedback_rating(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))

            customer_id = data.get('customer_id')
            product_id = data.get('product_id')
            product_order_id = data.get('product_order_id')
            rating = data.get('rating')  # Optional
            feedback = data.get('feedback', "")  # Optional

            # Validate required fields
            if not all([customer_id, product_id, product_order_id]):
                return JsonResponse({
                    "error": "customer_id, product_id, and product_order_id are required.",
                    "status_code": 400
                }, status=400)

            # Fetch related objects
            try:
                customer = CustomerRegisterDetails.objects.get(id=customer_id)
                product = ProductsDetails.objects.get(id=product_id)
                admin = product.admin  # Assuming ProductsDetails has 'admin' FK

                # Get payment using product_order_id
                payment = PaymentDetails.objects.filter(
                    customer=customer, product_order_id=product_order_id
                ).first()
                if not payment:
                    return JsonResponse({
                        "error": "Payment not found for given product_order_id.",
                        "status_code": 404
                    }, status=404)

                # Find matching order_product ID from payment.order_product_ids list
                order_product = OrderProducts.objects.filter(
                    id__in=payment.order_product_ids,
                    product=product,
                    customer=customer
                ).first()
                if not order_product:
                    return JsonResponse({
                        "error": "Matching order product not found.",
                        "status_code": 404
                    }, status=404)

            except Exception as e:
                return JsonResponse({
                    "error": f"Related object fetch error: {str(e)}",
                    "status_code": 404
                }, status=404)

            # Check if feedback already exists
            existing_feedback = FeedbackRating.objects.filter(
                customer=customer, product=product, order_product=order_product
            ).first()
            if existing_feedback:
                return JsonResponse({
                    "error": "Feedback already submitted for this product and order.",
                    "status_code": 400
                }, status=400)
            current_time = datetime.utcnow() + timedelta(hours=5, minutes=30)
            # formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")

            # Create feedback
            FeedbackRating.objects.create(
                admin=admin,
                customer=customer,
                payment=payment,
                order_product=order_product,
                order_id=product_order_id,
                product=product,
                category=product.category.category_name if product.category else "",
                sub_category=product.sub_category.sub_category_name if product.sub_category else "",
                rating=rating if rating else None,
                feedback=feedback,
                created_at=current_time
            )
            # current_time = datetime.utcnow() + timedelta(hours=5, minutes=30)
            # formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")


            return JsonResponse({
                "message": "Feedback submitted successfully.",
                "status_code": 201,
                "customer_id":customer_id,
                "submitted_at": current_time
            }, status=201)

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

    else:
        return JsonResponse({
            "error": "Invalid HTTP method. Only POST allowed.",
            "status_code": 405
        }, status=405)


# @csrf_exempt
# def submit_feedback_rating(request):
#     if request.method == "POST":
#         try:
#             data = json.loads(request.body.decode("utf-8"))

#             customer_id = data.get('customer_id')
#             product_id = data.get('product_id')
#             product_order_id = data.get('product_order_id')
#             rating = data.get('rating')  # Optional
#             feedback = data.get('feedback', "")  # Optional

#             # Validate required fields
#             if not all([customer_id, product_id, product_order_id]):
#                 return JsonResponse({
#                     "error": "customer_id, product_id, and product_order_id are required.",
#                     "status_code": 400
#                 }, status=400)

#             # Fetch related objects
#             try:
#                 customer = CustomerRegisterDetails.objects.get(id=customer_id)
#                 product = ProductsDetails.objects.get(id=product_id)
#                 admin = product.admin  # Assuming ProductsDetails has 'admin' FK

#                 # Get payment using product_order_id
#                 payment = PaymentDetails.objects.filter(
#                     customer=customer, product_order_id=product_order_id
#                 ).first()
#                 if not payment:
#                     return JsonResponse({
#                         "error": "Payment not found for given product_order_id.",
#                         "status_code": 404
#                     }, status=404)

#                 # Find matching order_product ID from payment.order_product_ids list
#                 order_product = OrderProducts.objects.filter(
#                     id__in=payment.order_product_ids,
#                     product=product,
#                     customer=customer
#                 ).first()
#                 if not order_product:
#                     return JsonResponse({
#                         "error": "Matching order product not found.",
#                         "status_code": 404
#                     }, status=404)

#             except Exception as e:
#                 return JsonResponse({
#                     "error": f"Related object fetch error: {str(e)}",
#                     "status_code": 404
#                 }, status=404)

#             # Check if feedback already exists
#             existing_feedback = FeedbackRating.objects.filter(
#                 customer=customer, product=product, order_product=order_product
#             ).first()
#             if existing_feedback:
#                 return JsonResponse({
#                     "error": "Feedback already submitted for this product and order.",
#                     "status_code": 400
#                 }, status=400)
#             current_time = datetime.utcnow() + timedelta(hours=5, minutes=30)
#             # formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")

#             # Create feedback
#             FeedbackRating.objects.create(
#                 admin=admin,
#                 customer=customer,
#                 payment=payment,
#                 order_product=order_product,
#                 order_id=product_order_id,
#                 product=product,
#                 category=product.category.category_name if product.category else "",
#                 sub_category=product.sub_category.sub_category_name if product.sub_category else "",
#                 rating=rating if rating else None,
#                 feedback=feedback,
#                 created_at=current_time
#             )
#             # current_time = datetime.utcnow() + timedelta(hours=5, minutes=30)
#             # formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")


#             return JsonResponse({
#                 "message": "Feedback submitted successfully.",
#                 "status_code": 201,
#                 "customer_id":customer_id,
#                 "submitted_at": current_time
#             }, status=201)

#         except json.JSONDecodeError:
#             return JsonResponse({
#                 "error": "Invalid JSON format.",
#                 "status_code": 400
#             }, status=400)

#         except Exception as e:
#             return JsonResponse({
#                 "error": f"Server error: {str(e)}",
#                 "status_code": 500
#             }, status=500)

#     else:
#         return JsonResponse({
#             "error": "Invalid HTTP method. Only POST allowed.",
#             "status_code": 405
#         }, status=405)

# @csrf_exempt
# def filter_my_order(request):
#     if request.method != "POST":
#         return JsonResponse({"error": "Invalid HTTP method. Only POST is allowed.", "status_code": 405}, status=405)

#     try:
#         data = json.loads(request.body.decode("utf-8"))
#         customer_id = data.get('customer_id')
#         order_status_filter = data.get('delivery_status')
#         order_time_filter = data.get('order_time')

#         if not customer_id:
#             return JsonResponse({"error": "customer_id is required.", "status_code": 400}, status=400)

#         # Filter by customer_id
#         payments = PaymentDetails.objects.filter(customer_id=customer_id)

#         # Dynamic year filters (keep last 4 years + older)
#         available_years = payments.dates('created_at', 'year', order='DESC')
#         year_options = ["Last 30 days"] + [dt.year for dt in available_years if dt.year >= datetime.now().year - 3] + ["Older"]


#         # Dynamic time filtering
#         now = datetime.now()
#         if order_time_filter:
#             if order_time_filter == "Last 30 days":
#                 payments = payments.filter(created_at__gte=now - timedelta(days=30))
#             elif order_time_filter == "Older":
#                 payments = payments.filter(created_at__lt=datetime(now.year - 3, 1, 1))
#             elif order_time_filter.isdigit():
#                 payments = payments.filter(created_at__year=int(order_time_filter))

#         payments = payments.order_by('-created_at')

#         if not payments.exists():
#             return JsonResponse({"error": "No order details found.", "status_code": 404}, status=404)

#         payment_list = []
#         total_matched_order_products = 0

#         for payment in payments:
#             order_ids = payment.order_product_ids
#             order_products = OrderProducts.objects.filter(id__in=order_ids)

#             # Apply order status filter if provided
#             if order_status_filter:
#                 order_products = order_products.filter(delivery_status=order_status_filter)

#             order_product_list = []
#             for order in order_products:
#                 product = ProductsDetails.objects.filter(id=order.product_id).first()
#                 product_image = product.product_images[0] if product and product.product_images else ""

#                 order_product_list.append({
#                     "order_product_id": order.id,
#                     "quantity": order.quantity,
#                     "price": order.price,
#                     "gst": f"{int(product.gst or 0)}%",
#                     "discount": f"{int(product.discount)}%" if product.discount else "0%",
#                     "final_price": round(float(product.price) - (float(product.price) * float(product.discount or 0) / 100), 2),
#                     "order_status": order.order_status,
#                     # "shipping_status":order.shipping_status,
#                     "delivery_status":order.delivery_status,
#                     "product_id": order.product_id,
#                     "product_image": product_image,
#                     "product_name": product.product_name
#                 })

#             # # Skip payment if no products matched the order status filter
#             # if order_status_filter and not order_product_list:
#             #     continue
#             if order_product_list:
#                 total_matched_order_products += len(order_product_list)
#             else:
#                 if order_status_filter:
#                     continue  # Skip payments where no product matches the delivery status


#             address_data = []
#             if payment.customer_address_id:
#                 address_obj = CustomerAddress.objects.filter(id=payment.customer_address_id).first()
#                 if address_obj:
#                     address_data.append({
#                         "address_id": address_obj.id,
#                         "customer_name": f"{address_obj.first_name} {address_obj.last_name}",
#                         "email": address_obj.email,
#                         "mobile_number": address_obj.mobile_number,
#                         "alternate_mobile": address_obj.alternate_mobile,
#                         "address_type": address_obj.address_type,
#                         "pincode": address_obj.pincode,
#                         "street": address_obj.street,
#                         "landmark": address_obj.landmark,
#                         "village": address_obj.village,
#                         "mandal": address_obj.mandal,
#                         "postoffice": address_obj.postoffice,
#                         "district": address_obj.district,
#                         "state": address_obj.state,
#                         "country": address_obj.country,
#                     })

#             payment_list.append({
#                 # "razorpay_order_id": payment.razorpay_order_id,
#                 "customer_name": f"{payment.customer.first_name} {payment.customer.last_name}",
#                 "email": payment.customer.email,
#                 "mobile_number": payment.customer.mobile_no,
#                 "payment_mode": payment.payment_mode,
#                 "total_quantity": payment.quantity,
#                 "total_amount": payment.total_amount,
#                 "payment_date": payment.created_at.strftime("%Y-%m-%d %H:%M:%S"),
#                 "time_filters": year_options,
#                 "product_order_id": payment.product_order_id,
#                 "customer_address": address_data,
#                 "order_products": order_product_list
#             })

#         if order_status_filter and total_matched_order_products == 0:
#             return JsonResponse({
#                 "error": "No products found for the selected delivery status.",
#                 "status_code": 404,
#                 "time_filters": year_options
#             }, status=404)
#         if not payment_list:
#             return JsonResponse({"error": "No order details match filters.", "status_code": 404}, status=404)

#         return JsonResponse({
#             "message": "Filtered Orders Retrieved Successfully.",
#             "payments": payment_list,
#             "status_code": 200,
#             "customer_id": str(customer_id)
#         }, status=200)

#     except Exception as e:
#         return JsonResponse({"error": str(e), "status_code": 500}, status=500)




@csrf_exempt
def edit_feedback_rating(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))

            customer_id = data.get('customer_id')
            product_id = data.get('product_id')
            product_order_id = data.get('product_order_id')
            rating = data.get('rating')  # Optional
            feedback = data.get('feedback')  # Optional

            # Validate required fields
            if not all([customer_id, product_id, product_order_id]):
                return JsonResponse({
                    "error": "customer_id, product_id, and product_order_id are required.",
                    "status_code": 400
                }, status=400)

            # Fetch related objects
            try:
                customer = CustomerRegisterDetails.objects.get(id=customer_id)
                product = ProductsDetails.objects.get(id=product_id)

                payment = PaymentDetails.objects.filter(
                    customer=customer, product_order_id=product_order_id
                ).first()
                if not payment:
                    return JsonResponse({
                        "error": "Payment not found for given product_order_id.",
                        "status_code": 404
                    }, status=404)

                order_product = OrderProducts.objects.filter(
                    id__in=payment.order_product_ids,
                    product=product,
                    customer=customer
                ).first()
                if not order_product:
                    return JsonResponse({
                        "error": "Matching order product not found.",
                        "status_code": 404
                    }, status=404)

            except Exception as e:
                return JsonResponse({
                    "error": f"Related object fetch error: {str(e)}",
                    "status_code": 404
                }, status=404)

            # Fetch existing feedback
            existing_feedback = FeedbackRating.objects.filter(
                customer=customer,
                product=product,
                order_product=order_product
            ).first()

            if not existing_feedback:
                return JsonResponse({
                    "error": "No existing feedback found to update.",
                    "status_code": 404
                }, status=404)

            # Update feedback fields
            if rating is not None:
                existing_feedback.rating = rating
            if feedback is not None:
                existing_feedback.feedback = feedback

            existing_feedback.updated_at = datetime.utcnow() + timedelta(hours=5, minutes=30)
            existing_feedback.save()

            return JsonResponse({
                "message": "Feedback updated successfully.",
                "status_code": 200,
                "customer_id": customer_id,
                "updated_at": existing_feedback.updated_at,
                "customer_id":customer_id
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

    else:
        return JsonResponse({
            "error": "Invalid HTTP method. Only POST allowed.",
            "status_code": 405
        }, status=405)

    

@csrf_exempt
def view_rating(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))

            customer_id = data.get('customer_id')

            # Validate required field
            if not customer_id:
                return JsonResponse({
                    "error": "customer_id is required.",
                    "status_code": 400
                }, status=400)

            # Fetch customer object
            customer = CustomerRegisterDetails.objects.get(id=customer_id)

            feedbacks = FeedbackRating.objects.filter(customer=customer)

            if not feedbacks.exists():
                return JsonResponse({
                    "error": "No feedback found for this customer.",
                    "status_code": 404
                }, status=404)

            rating_list = []
            for feedback in feedbacks:
                rating_list.append({
                    "rating": feedback.rating,
                    "product_id": feedback.product.id,
                    "product_name": feedback.product.product_name,
                    "order_product_id": feedback.order_product.id,
                    "order_id": feedback.order_id,
                })

            return JsonResponse({
                "ratings": rating_list,
                "customer_id": customer_id,
                "status_code": 200
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

    else:
        return JsonResponse({
            "error": "Invalid HTTP method. Only POST allowed.",
            "status_code": 405
        }, status=405)
