from django.shortcuts import render, redirect, get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.contrib.auth import authenticate, login, logout 
from django.views.decorators.csrf import csrf_exempt,csrf_protect
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from .models import CustomUser, OTP,Specialization, ContactMessage, QuickContact, Feedback, PatientProfile, DoctorProfile, HospitalClinicProfile, Appointment, HospitalDoctors
from .serializers import PatientRegistrationSerializer,HospitalRegistrationSerializer, DoctorRegistrationSerializer
from symptoms.models import BodyPart
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Prefetch
from django.views.decorators.http import require_POST
from .email_utils import send_otp_email
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
from .forms import SubscriptionPlanForm
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse
from django.views.decorators.http import require_POST
from .models import SubscriptionPlan, UserSubscription
from django.utils import timezone
from datetime import datetime as dt, time as dt_time
from .pdf_utils import generate_appointment_pdf
import json
import logging
logger = logging.getLogger("accounts")


def has_active_subscription(user):
    """
    Check if user has an active subscription based on date ranges (not DB field).
    Returns True if user has at least one subscription where start_date <= today <= end_date
    """
    from django.utils import timezone
    today = timezone.now().date()
    active_sub = user.subscriptions.filter(
        start_date__lte=today,
        end_date__gte=today
    ).first()
    return active_sub is not None


def get_subscription_data(user):
    """
    Get subscription status and dates for a user.
    Returns dict with subscription_active, subscription_start, subscription_end
    """
    from django.utils import timezone
    today = timezone.now().date()
    
    # Get active subscription (within date range)
    active_sub = user.subscriptions.filter(
        start_date__lte=today,
        end_date__gte=today
    ).first()
    
    if active_sub:
        return {
            'subscription_active': True,
            'subscription_start': active_sub.start_date,
            'subscription_end': active_sub.end_date,
            'subscription_obj': active_sub
        }
    
    # If no active, get the most recent one for display
    recent_sub = user.subscriptions.order_by('-end_date').first()
    return {
        'subscription_active': False,
        'subscription_start': recent_sub.start_date if recent_sub else None,
        'subscription_end': recent_sub.end_date if recent_sub else None,
        'subscription_obj': recent_sub
    }

def patient_signup(request):

    if request.user.is_authenticated:
        return redirect('home') 

    return render(request, 'accounts/patient-signup.html')


def hospital_signup(request):

    if request.user.is_authenticated:
        return redirect('home') 

    return render(request, 'accounts/hospital-signup.html')

def doctor_signup(request):
    if request.user.is_authenticated:
        return redirect('home')

    specializations = Specialization.objects.all().order_by("name")
    return render(request, 'accounts/doctor-signup.html', {"specializations": specializations})


class EmailUniqueCheckAPIView(APIView):
    def post(self, request):
        email = request.data.get("email", "").strip()
        if CustomUser.objects.filter(email=email).exists():
            return Response({"error": "This email is already registered"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": "Email is available"}, status=status.HTTP_200_OK)


class ContactNumberUniqueCheckAPIView(APIView):
    def post(self, request):
        contact_number = request.data.get("contact_number", "").strip()
        if CustomUser.objects.filter(phone_number=contact_number).exists():
            return Response({"error": "This contact number is already registered"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": "Contact number is available"}, status=status.HTTP_200_OK)


class PatientRegisterAPIView(APIView):
    def post(self, request):
        logger.info(f"Received patient registration request: {request.data}")

        serializer = PatientRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            logger.info(f"User registered successfully: {user.email}")

            OTP.objects.filter(user=user).delete()
            otp = OTP.create_or_update_otp(user=user, otp_type="email", validity_minutes=5)

            try:
                send_otp_email(user, otp.code)
                logger.info(f"OTP sent to user: {user.email} {user.username}")
            except Exception as e:
                logger.exception(f"Failed to send OTP to {user.email} {user.username}: {e}")
                # return Response(
                #     {"error": "User registered but failed to send OTP."},
                #     status=status.HTTP_500_INTERNAL_SERVER_ERROR,``
                # )
                pass

            return Response({"message": "User registered. OTP sent."}, status=status.HTTP_201_CREATED)

        logger.warning(f"Patient registration failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class HospitalRegisterAPIView(APIView):
    """
    Registers a hospital/clinic user as a soft user (is_deleted=True) and sends OTP.
    Admin must later verify profile to activate (is_active).
    """
    def post(self, request):
        logger.info(f"Received hospital registration request: {request.data}")
        serializer = HospitalRegistrationSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()
            logger.info(f"Hospital user created (soft): {user.email}")

            # Remove any old OTPs and create new
            OTP.objects.filter(user=user).delete()
            otp = OTP.create_or_update_otp(user=user, otp_type="email", validity_minutes=5)

            try:
                send_otp_email(user, otp.code)
                logger.info(f"OTP sent to hospital user: {user.email}")

            except Exception as e:
                logger.exception(f"Failed to send OTP to hospital {user.email}: {e}")

            return Response({"message": "Hospital registered. OTP sent for verification."}, status=status.HTTP_201_CREATED)

        logger.warning(f"Hospital registration failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class DoctorRegisterAPIView(APIView):
    """
    Registers a doctor user as a soft user (is_deleted=True) and sends OTP.
    Admin must later verify profile to activate (is_active).
    """
    def post(self, request):
        logger.info(f"Received doctor registration request: {request.data}")
        data = request.data.copy()
        specs = data.get("specializations")
        if specs and isinstance(specs, str):
            data.setlist("specializations", [s for s in specs.split(",") if s.strip()])
        serializer = DoctorRegistrationSerializer(data=data)

        if serializer.is_valid():
            user = serializer.save()
            logger.info(f"Doctor user created (soft): {user.email}")

            # Remove any old OTPs and create new
            OTP.objects.filter(user=user).delete()
            otp = OTP.create_or_update_otp(user=user, otp_type="email", validity_minutes=5)
            
            try:
                send_otp_email(user, otp.code)
                logger.info(f"OTP sent to doctor user: {user.email}")

            except Exception as e:
                logger.exception(f"Failed to send OTP to doctor {user.email}: {e}")

            return Response({"message": "Doctor registered. OTP sent for verification."}, status=status.HTTP_201_CREATED)

        logger.warning(f"Doctor registration failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    

class VerifyOtpAPIView(APIView):
    def post(self, request):
        email = request.data.get("email")
        code = request.data.get("otp")
        user_type = request.data.get("user_type")  

        if not email or not code or not user_type:
            return Response({"error": "Email, OTP and user_type are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.get(email=email)
            otp = OTP.objects.get(user=user)

        except (CustomUser.DoesNotExist, OTP.DoesNotExist):
            return Response({"error": "Invalid user/OTP"}, status=status.HTTP_400_BAD_REQUEST)

        if otp.is_valid() and otp.code == code:
            otp.is_used = True
            otp.save()

            user.is_deleted = False
            user.is_active = True

            # Apply rules based on user_type
            if user_type == "patient":
                user.is_verified = True
            elif user_type in ["doctor", "hospital"]:
                user.is_verified = False  # requires admin approval
            else:
                return Response({"error": "Invalid user_type"}, status=status.HTTP_400_BAD_REQUEST)

            user.save()

            msg = (
                "Account verified successfully"
                if user_type == "patient"
                else "Account created successfully. Await admin verification and approval."
            )
            return Response({"message": msg}, status=status.HTTP_200_OK)

        return Response({"error": "Invalid or expired OTP"}, status=status.HTTP_400_BAD_REQUEST)


class ResendOtpAPIView(APIView):
    def post(self, request):
        email = request.data.get("email")
        logger.info(f"[ResendOTP] Request received for email: {email}")

        try:
            user = CustomUser.objects.get(email=email)
            logger.info(f"[ResendOTP] Found user: {user.email}")

        except CustomUser.DoesNotExist:
            logger.error(f"[ResendOTP] User not found: {email}")
            return Response({"error": "User not found"}, status=status.HTTP_400_BAD_REQUEST)

        OTP.objects.filter(user=user).delete()
        logger.info(f"[ResendOTP] Deleted existing OTPs for user: {email}")

        otp = OTP.create_or_update_otp(user=user, otp_type="email", validity_minutes=5)
        logger.info(f"[ResendOTP] Created new OTP: {otp.code} for user: {email}")

        try:
            send_otp_email(user, otp.code)
            logger.info(f"[ResendOTP] OTP email sent to: {email}")

        except Exception as e:
            logger.exception(f"[ResendOTP] Failed to send OTP email to {email}: {e}")
            pass

        return Response({"message": "New OTP sent"}, status=status.HTTP_200_OK)


class CancelRegistrationAPIView(APIView):
    def post(self, request):
        email = request.data.get("email")
        logger.info(f"Cancellation request for email: {email}")

        try:
            user = CustomUser.objects.get(email=email, is_deleted=True)
            user.delete()
            logger.info(f"Cancelled and deleted user: {email}")
            return Response({"message": "Registration cancelled"}, status=status.HTTP_200_OK)
        
        except CustomUser.DoesNotExist:
            logger.warning(f"Cancellation failed, user not found or already active: {email}")
            return Response({"error": "User not found or already active"}, status=status.HTTP_400_BAD_REQUEST)
        


@csrf_protect
def login_view(request):
    
    if request.user.is_authenticated:
        return redirect('home') 

    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        logger.info(f"[User Login]: email - {email}, Password- {password}")

        if not email or not password:
            return JsonResponse({"detail": "Email and password are required."}, status=400)

        # Step 1: Check user existence
        try:
            user = CustomUser.objects.get(email=email, is_deleted=False)
        except CustomUser.DoesNotExist:
            return JsonResponse({"detail": "User does not exist"}, status=404)

        # Step 2: Check if active
        if not user.is_active:
            return JsonResponse(
                {"detail": "Account inactive please contact support team"},
                status=403,
            )

        # Step 3: Authenticate
        user = authenticate(request, email=email, password=password)
        if user is None:
            return JsonResponse({"detail": "Invalid credentials"}, status=401)

        # Step 4: Login (creates session)
        login(request, user)

        # Step 5: Store extra fields in session
        request.session["user_type"] = user.user_type
        request.session["is_verified"] = user.is_verified
        request.session["is_active"] = user.is_active
        request.session["is_staff"] = user.is_staff
        request.session["email"] = user.email

        return JsonResponse(
            {
                "detail": "Login successful",
                "redirect_url": "/",
            },
            status=200,
        )

    return render(request, "accounts/login.html")


# ---------------- Forgot Password APIs ----------------

class ForgotPasswordCheckAPIView(APIView):
    """
    Step 1: check user exists, is not soft-deleted and is active.
    If OK -> create/update OTP and send by email.
    """

    def post(self, request):
        email = request.data.get("email", "").strip().lower()

        if not email:
            logger.warning("[ForgotPassword] Email not provided in request")
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.get(email=email, is_deleted=False)

        except CustomUser.DoesNotExist:
            logger.warning(f"[ForgotPassword] User not found for email: {email}")
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        if not user.is_active:
            logger.warning(f"[ForgotPassword] Account inactive for email: {email}")
            return Response({"error": "Account is not active. Contact support."}, status=status.HTTP_403_FORBIDDEN)

        # create / overwrite OTP
        OTP.objects.filter(user=user).delete()
        otp = OTP.create_or_update_otp(user=user, otp_type="email", validity_minutes=5)

        try:
            send_otp_email(user, otp.code)
            logger.info(f"[ForgotPassword] Sent OTP to {email}")
            
        except Exception as e:
            logger.exception(f"[ForgotPassword] Failed to send OTP email to {email}: {e}")
            pass

        return Response({"message": "OTP sent to registered email."}, status=status.HTTP_200_OK)


class ForgotPasswordVerifyOtpAPIView(APIView):
    """
    Step 2: verify OTP for the forgot-password flow.
    If valid return success (frontend will allow user to enter new password).
    """

    def post(self, request):
        email = request.data.get("email", "").strip().lower()
        code = request.data.get("otp", "").strip()

        if not email or not code:
            logger.warning("OTP verification failed: Missing email or OTP. Request data: %s", request.data)
            return Response({"error": "Email and OTP required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.get(email=email, is_deleted=False)
            otp = OTP.objects.get(user=user)

        except CustomUser.DoesNotExist:
            logger.error(f"OTP verification failed: User with email '{email}' not found.")
            return Response({"error": "Invalid user or OTP"}, status=status.HTTP_400_BAD_REQUEST)
        
        except OTP.DoesNotExist:
            logger.error(f"OTP verification failed: OTP not found for user '{email}'.")
            return Response({"error": "Invalid user or OTP"}, status=status.HTTP_400_BAD_REQUEST)

        if otp.is_valid() and otp.code == code:
            logger.info(f"OTP verified successfully for user '{email}'.")
            return Response({"message": "OTP verified. Proceed to reset password."}, status=status.HTTP_200_OK)

        logger.warning(f"OTP verification failed: Invalid or expired OTP for user '{email}'.")
        return Response({"error": "Invalid or expired OTP"}, status=status.HTTP_400_BAD_REQUEST)


class ForgotPasswordResetAPIView(APIView):
    """
    Step 3: reset password. Requires email, otp and new_password.
    Sets password using set_password (hashed) and marks otp as used.
    """

    def post(self, request):
        email = request.data.get("email", "").strip().lower()
        code = request.data.get("otp", "").strip()
        new_password = request.data.get("new_password", "")

        if not email or not code or not new_password:
            logger.warning(f"[ForgotPasswordReset] Missing required fields: email={email}, otp={bool(code)}")

        try:
            user = CustomUser.objects.get(email=email, is_deleted=False)
            otp = OTP.objects.get(user=user)

        except (CustomUser.DoesNotExist, OTP.DoesNotExist):
            logger.warning(f"[ForgotPasswordReset] Invalid user or OTP for email={email}")
            return Response(
                {"error": "Invalid user or OTP"}, 
                status=status.HTTP_400_BAD_REQUEST
                )

        if not (otp.is_valid() and otp.code == code):
            logger.warning(f"[ForgotPasswordReset] Invalid or expired OTP for email={email}")
            return Response({"error": "Invalid or expired OTP"}, status=status.HTTP_400_BAD_REQUEST)

        # Validate password strength server-side (optional — you already have validators)
        try:
            user.set_password(new_password)  # secure hashing
            user.save()

            # mark OTP used
            otp.is_used = True
            otp.save()

            logger.info(f"[ForgotPasswordReset] Password reset successful for email={email}")
            return Response({"message": "Password reset successful"}, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.exception(f"[ForgotPasswordReset] Failed to reset password for {email}: {e}")
            return Response({"error": "Failed to reset password"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ForgotPasswordResendOtpAPIView(APIView):
    """
    Resend OTP for forgot password (overwrite existing OTP).
    """

    def post(self, request):
        email = request.data.get("email", "").strip().lower()

        if not email:
            logger.warning("ForgotPasswordResendOtpAPIView: Missing email in request")
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.get(email=email, is_deleted=False)

        except CustomUser.DoesNotExist:
            logger.info(f"ForgotPasswordResendOtpAPIView: User not found for email={email}")
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        OTP.objects.filter(user=user).delete()
        otp = OTP.create_or_update_otp(user=user, otp_type="email", validity_minutes=5)
        logger.info(f"ForgotPasswordResendOtpAPIView: OTP deleted for user_id={user.id}, email={email}")

        try:
            send_otp_email(user, otp.code)
            logger.info(f"[ForgotPasswordResend] Sent OTP to {email}")
        except Exception as e:
            logger.exception(f"[ForgotPasswordResend] Failed to send OTP to {email}: {e}")
            pass

        return Response({"message": "New OTP sent"}, status=status.HTTP_200_OK)


class ForgotPasswordCancelAPIView(APIView):
    """
    Cancel forgot-password flow — delete the OTP so the flow is aborted.
    """
    def post(self, request):
        email = request.data.get("email", "").strip().lower()

        if not email:
            logger.warning("ForgotPasswordCancel: Missing email in request")
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = CustomUser.objects.get(email=email, is_deleted=False)

        except CustomUser.DoesNotExist:
            logger.info(f"ForgotPasswordCancel: User not found for email={email}")
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        OTP.objects.filter(user=user).delete()
        logger.info(f"ForgotPasswordCancel: OTP deleted for user_id={user.id}, email={email}")

        return Response({"message": "Forgot password flow cancelled"}, status=status.HTTP_200_OK)


def reset_password_view(request):
    return render(request, 'accounts/reset-password.html')

def logout_view(request):
    logout(request)
    request.session.flush()
    
    return redirect("login")


def doctor_dashboard(request):
    """
    Doctor Dashboard - displays account info, availability, and subscription status
    """
    if not request.user.is_authenticated or request.user.user_type != 'doctor':
        return redirect('login')
    
    try:
        doctor_profile = request.user.doctor_profile
    except DoctorProfile.DoesNotExist:
        return redirect('login')
    
    # Get latest subscription (ordered by creation date to get most recent request)
    latest_subscription = request.user.subscriptions.filter(
        subscription_plan__user_type='doctor'
    ).order_by('-created_at').first()
    
    # Log subscription data for debugging
    logger.info(f"Doctor Dashboard - User: {request.user.email}, Subscription: {latest_subscription}")
    
    # Calculate subscription status and related data
    days_until_expiry = None
    subscription_status = None
    show_no_plan_alert = False
    can_buy_plan = False
    
    if latest_subscription:
        from django.utils import timezone
        today = timezone.now().date()
        end_date = latest_subscription.end_date
        start_date = latest_subscription.start_date
        days_diff = (end_date - today).days
        
        # Determine status based on is_active flag and dates
        if not latest_subscription.is_active:
            # Subscription not yet activated by admin
            if latest_subscription.status == 'pending':
                subscription_status = 'pending_verification'
                logger.info("Subscription pending admin verification")
            elif latest_subscription.status == 'rejected':
                subscription_status = 'rejected'
                can_buy_plan = True
                show_no_plan_alert = True
                logger.info("Subscription rejected by admin")
            else:
                subscription_status = 'inactive'
                show_no_plan_alert = True
                can_buy_plan = True
        elif start_date > today:
            # Future subscription (active but not started yet)
            subscription_status = 'future'
            logger.info(f"Future subscription starting on {start_date}")
        elif days_diff < 0:
            # Expired
            days_until_expiry = abs(days_diff)
            subscription_status = 'expired'
            show_no_plan_alert = True
            can_buy_plan = True
            logger.info(f"Subscription expired {days_until_expiry} days ago")
        elif days_diff == 0:
            # Expires today
            days_until_expiry = 0
            subscription_status = 'expires_today'
            logger.info("Subscription expires today")
        elif days_diff <= 7:
            # Expiring within 7 days
            days_until_expiry = days_diff
            subscription_status = 'expiring_soon'
            logger.warning(f"Subscription expiring in {days_until_expiry} days")
        else:
            # Active and not expiring soon
            days_until_expiry = days_diff
            subscription_status = 'active'
            logger.info(f"Subscription active, expires in {days_until_expiry} days")
    else:
        # No subscription at all
        subscription_status = 'none'
        show_no_plan_alert = True
        can_buy_plan = True
        logger.info("No subscription found for user")
    
    # Get pending appointments for the doctor
    filter_date = request.GET.get('pendingAppointmentsDateFilter')
    from django.utils import timezone
    today = timezone.now().date()
    pending_appointments_qs = Appointment.objects.filter(
        doctor=doctor_profile,
        status='PENDING'
    )
    if filter_date:
        pending_appointments_qs = pending_appointments_qs.filter(appointment_date=filter_date)
    else:
        pending_appointments_qs = pending_appointments_qs.filter(appointment_date=today)
    pending_appointments = pending_appointments_qs.select_related('patient__user').order_by('-created_at')
    
    context = {
        'doctor': doctor_profile,
        'user': request.user,
        'subscription': latest_subscription,
        'days_until_expiry': days_until_expiry,
        'subscription_status': subscription_status,
        'show_no_plan_alert': show_no_plan_alert,
        'can_buy_plan': can_buy_plan,
        'pending_appointments': pending_appointments,
        'pending_count': pending_appointments.count(),
        'filter_date': filter_date,
        'today': today,
    }
    
    logger.debug(f"Doctor Dashboard Context - Status: {subscription_status}, Days: {days_until_expiry}, Show Alert: {show_no_plan_alert}")
    
    return render(request, 'accounts/doctor-dashboard.html', context)


@csrf_exempt
def toggle_doctor_availability(request):
    """
    AJAX endpoint to toggle doctor availability
    """
    if not request.user.is_authenticated or request.user.user_type != 'doctor':
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        from django.utils import timezone
        doctor_profile = request.user.doctor_profile
        doctor_profile.is_available = not doctor_profile.is_available
        doctor_profile.availability_last_updated = timezone.now()
        doctor_profile.save(update_fields=['is_available', 'availability_last_updated'])
        
        return JsonResponse({
            'status': 'success',
            'is_available': doctor_profile.is_available,
            'last_updated': doctor_profile.availability_last_updated.isoformat(),
            'message': 'Availability updated successfully'
        })
    except DoctorProfile.DoesNotExist:
        return JsonResponse({'error': 'Doctor profile not found'}, status=404)
    except Exception as e:
        logger.error(f"Error toggling doctor availability: {str(e)}")
        return JsonResponse({'error': 'An error occurred'}, status=500)


def patient_dashboard(request):
    """
    Patient Dashboard - displays account info, subscription status, and appointments
    """
    if not request.user.is_authenticated or request.user.user_type != 'patient':
        return redirect('login')

    # Fetch patient profile if needed (currently not used but available)
    try:
        patient_profile = request.user.patient_profile
    except Exception:
        patient_profile = None

    # Get latest subscription (ordered by creation date to get most recent request)
    latest_subscription = request.user.subscriptions.filter(
        subscription_plan__user_type='patient'
    ).order_by('-created_at').first()
    
    logger.info(f"Patient Dashboard - User: {request.user.email}, Subscription: {latest_subscription}")
    
    # Calculate subscription status and related data
    days_until_expiry = None
    subscription_status = None
    show_no_plan_alert = False
    can_buy_plan = False
    
    if latest_subscription:
        from django.utils import timezone
        today = timezone.now().date()
        end_date = latest_subscription.end_date
        start_date = latest_subscription.start_date
        days_diff = (end_date - today).days
        
        # Determine status based on is_active flag and dates
        if not latest_subscription.is_active:
            # Subscription not yet activated by admin
            if latest_subscription.status == 'pending':
                subscription_status = 'pending_verification'
                logger.info("Subscription pending admin verification")
            elif latest_subscription.status == 'rejected':
                subscription_status = 'rejected'
                can_buy_plan = True
                show_no_plan_alert = True
                logger.info("Subscription rejected by admin")
            else:
                subscription_status = 'inactive'
                show_no_plan_alert = True
                can_buy_plan = True
        elif start_date > today:
            # Future subscription (active but not started yet)
            subscription_status = 'future'
            logger.info(f"Future subscription starting on {start_date}")
        elif days_diff < 0:
            # Expired
            days_until_expiry = abs(days_diff)
            subscription_status = 'expired'
            show_no_plan_alert = True
            can_buy_plan = True
            logger.info(f"Subscription expired {days_until_expiry} days ago")
        elif days_diff == 0:
            # Expires today
            days_until_expiry = 0
            subscription_status = 'expires_today'
            logger.info("Subscription expires today")
        elif days_diff <= 7:
            # Expiring within 7 days
            days_until_expiry = days_diff
            subscription_status = 'expiring_soon'
            logger.warning(f"Subscription expiring in {days_until_expiry} days")
        else:
            # Active and not expiring soon
            days_until_expiry = days_diff
            subscription_status = 'active'
            logger.info(f"Subscription active, expires in {days_until_expiry} days")
    else:
        # No subscription at all
        subscription_status = 'none'
        show_no_plan_alert = True
        can_buy_plan = True
        logger.info("No subscription found for patient")

    # Get patient's appointments with pagination
    # Fetch both doctor and hospital bookings
    appointments_list = Appointment.objects.filter(
        patient=patient_profile
    ).select_related(
        'doctor__user', 
        'hospital'
    ).prefetch_related(
        'doctor__specializations'
    ).order_by('-created_at')
    
    # Pagination support (10 records per page)
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    
    page_number = request.GET.get('page', 1)
    paginator = Paginator(appointments_list, 10)  # 10 appointments per page
    
    try:
        appointments = paginator.page(page_number)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        appointments = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page of results
        appointments = paginator.page(paginator.num_pages)

    context = {
        'patient': patient_profile,
        'user': request.user,
        'subscription': latest_subscription,
        'days_until_expiry': days_until_expiry,
        'subscription_status': subscription_status,
        'show_no_plan_alert': show_no_plan_alert,
        'can_buy_plan': can_buy_plan,
        'appointments': appointments,
        'appointments_paginator': paginator,
    }
    
    logger.debug(f"Patient Dashboard Context - Status: {subscription_status}, Days: {days_until_expiry}, Show Alert: {show_no_plan_alert}")
    
    return render(request, 'accounts/patient-dashboard.html', context)


def download_appointment_pdf(request, appointment_id):
    """
    Download appointment as PDF
    Only allowed for patients to download their accepted appointments
    """
    try:
        if not request.user.is_authenticated or request.user.user_type != 'patient':
            return HttpResponse('Unauthorized', status=401)
        
        # Get patient profile
        patient_profile = request.user.patient_profile
        
        # Get appointment and verify it belongs to this patient
        appointment = Appointment.objects.get(id=appointment_id, patient=patient_profile)
        
        # Only allow download if status is ACCEPTED
        if appointment.status != 'ACCEPTED':
            return HttpResponse('Appointment not accepted', status=400)
        
        # Generate PDF
        pdf_buffer = generate_appointment_pdf(appointment)
        
        # Create response
        response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="appointment_{appointment_id}.pdf"'
        
        return response
    
    except Appointment.DoesNotExist:
        return HttpResponse('Appointment not found', status=404)
    except Exception as e:
        logger.error(f"Error downloading appointment PDF: {str(e)}")
        return HttpResponse('Error generating PDF', status=500)

def contact_us(request):
    # Get quick contact info
    quick_contact = QuickContact.objects.filter(is_active=True).first()
    
    # Pre-fill form data for logged-in users
    initial_data = {}
    if request.user.is_authenticated:
        # Get the proper display name based on user type
        display_name = ""
        if hasattr(request.user, 'patient_profile'):
            display_name = request.user.patient_profile.full_name
        elif hasattr(request.user, 'doctor_profile'):
            display_name = request.user.doctor_profile.doctor_name
        elif hasattr(request.user, 'hospital_profile'):
            display_name = request.user.hospital_profile.name
        else:
            display_name = request.user.username or request.user.email.split('@')[0]
        
        initial_data = {
            'name': display_name,
            'email': request.user.email,
            'phone': getattr(request.user, 'phone_number', '')
        }
    
    context = {
        'quick_contact': quick_contact,
        'initial_data': initial_data,
        'user': request.user
    }
    return render(request, 'contacts/contact_us.html', context)

@csrf_exempt
def submit_contact(request):
    if request.method == 'POST':
        try:
            # For authenticated users, use their actual data from the database
            if request.user.is_authenticated:
                # Get the proper display name based on user type
                if hasattr(request.user, 'patient_profile'):
                    name = request.user.patient_profile.full_name
                elif hasattr(request.user, 'doctor_profile'):
                    name = request.user.doctor_profile.doctor_name
                elif hasattr(request.user, 'hospital_profile'):
                    name = request.user.hospital_profile.name
                else:
                    name = request.user.username or request.user.email.split('@')[0]
                
                email = request.user.email
                phone = getattr(request.user, 'phone_number', '')
                
                subject = request.POST.get('subject')
                message_text = request.POST.get('message')
            else:
                # For non-authenticated users, use form data
                name = request.POST.get('name')
                email = request.POST.get('email')
                phone = request.POST.get('phone')
                subject = request.POST.get('subject')
                message_text = request.POST.get('message')
            
            # Validate required fields
            if not all([name, email, subject, message_text]):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Please fill all required fields.'
                })
            
            # Create contact message
            contact_message = ContactMessage(
                user=request.user if request.user.is_authenticated else None,
                name=name,
                email=email,
                phone=phone,
                subject=subject,
                message=message_text
            )
            contact_message.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Your message has been sent successfully! We will get back to you soon.'
            })
            
        except Exception as e:
            # Log the actual error for debugging
            logging.error(f"Error in submit_contact: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': f'There was an error sending your message: {str(e)}'
            })
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method.'
    })




def feedback(request):
    # Get all body parts for the multi-select
    body_parts = BodyPart.objects.all().order_by('name')
    
    # Pre-fill form data for logged-in users
    initial_data = {}
    if request.user.is_authenticated:
        initial_data = {
            'email': request.user.email,
            'phone': getattr(request.user, 'phone_number', ''),
        }
    
    context = {
        'body_parts': body_parts,
        'initial_data': initial_data,
        'user': request.user
    }
    return render(request, 'contacts/feedback.html', context)


@csrf_exempt
def submit_feedback(request):
    if request.method == 'POST':
        try:
            # For authenticated users, use their actual data from the database
            if request.user.is_authenticated:
                email = request.user.email
                phone = getattr(request.user, 'phone_number', '')
            else:
                # For non-authenticated users, use form data
                email = request.POST.get('email')
                phone = request.POST.get('phone')
            
            # Get other form data
            role = request.POST.get('role')
            age = request.POST.get('age')
            address = request.POST.get('address')
            selected_body_parts_ids = request.POST.getlist('selected_body_parts')
            symptoms_understanding = request.POST.get('symptoms_understanding')
            illness_suggestion = request.POST.get('illness_suggestion')
            helpful_doctor_suggestion = request.POST.get('helpful_doctor_suggestion')
            want_appointment_feature = request.POST.get('want_appointment_feature')
            improvement_suggestion = request.POST.get('improvement_suggestion')
            rate_us = request.POST.get('rate_us')
            
            # Validate required fields
            required_fields = {
                'email': email,
                'role': role,
                'symptoms_understanding': symptoms_understanding,
                'illness_suggestion': illness_suggestion,
                'helpful_doctor_suggestion': helpful_doctor_suggestion,
                'rate_us': rate_us,
            }
            
            missing_fields = [field for field, value in required_fields.items() if not value]
            if missing_fields:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Please fill all required fields: {", ".join(missing_fields)}'
                })
            
            # Create feedback instance
            feedback = Feedback(
                user=request.user if request.user.is_authenticated else None,
                email=email,
                phone=phone,
                role=role,
                age=age if age else None,
                address=address,
                symptoms_understanding=symptoms_understanding,
                illness_suggestion=illness_suggestion,
                helpful_doctor_suggestion=helpful_doctor_suggestion,
                want_appointment_feature=want_appointment_feature,
                improvement_suggestion=improvement_suggestion,
                rate_us=rate_us,
                is_anonymous=not request.user.is_authenticated
            )
            feedback.save()
            
            # Add selected body parts
            if selected_body_parts_ids:
                body_parts = BodyPart.objects.filter(id__in=selected_body_parts_ids)
                feedback.selected_body_parts.set(body_parts)
            
            return JsonResponse({
                'status': 'success',
                'message': 'Thank you for your valuable feedback! We appreciate your input in helping us improve our services.'
            })
            
        except Exception as e:
            # Log the actual error for debugging
            print(f"Error in submit_feedback: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': f'There was an error submitting your feedback: {str(e)}'
            })
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method.'
    })


def admin_dashboard(request):
    context = {
        'contact_count': ContactMessage.objects.count(),
        'feedback_count': Feedback.objects.count(),
        'patient_count': PatientProfile.objects.count(),
        'doctor_count': DoctorProfile.objects.count(),
        'hospital_count': HospitalClinicProfile.objects.count(),
    }
    return render(request, 'admin-user/admin-dashboard.html', context)


@staff_member_required
def admin_subscriptions_list(request):
    plans = []
    try:
        
        plans = SubscriptionPlan.objects.order_by('-created_at')
    except Exception:
        plans = []

    # show toasts after create/update via query params
    context = {
        'plans': plans,
        'created': request.GET.get('created'),
        'updated': request.GET.get('updated'),
        'deleted': request.GET.get('deleted')
    }
    return render(request, 'admin-user/subscription-plans-list.html', context)


@staff_member_required
def admin_subscription_create(request):
    
    if request.method == 'POST':
        form = SubscriptionPlanForm(request.POST, request.FILES)
        try:
            if form.is_valid():
                # Business rule: prevent multiple active plans per user_type
                user_type = form.cleaned_data.get('user_type')
                is_active = form.cleaned_data.get('is_active')

                if (
                    is_active and
                    SubscriptionPlan.objects.filter(
                        user_type=user_type,
                        is_active=True
                    ).exists()
                ):
                    form.add_error(
                        None,
                        'An active plan for this role already exists. '
                        'Deactivate it before creating a new one.'
                    )
                else:
                    plan = form.save(commit=False)

                    # ensure is_active default True if not explicitly provided
                    if plan.is_active is None:
                        plan.is_active = True

                    plan.save()
                    return redirect(
                        reverse('admin-subscriptions-list') + '?created=1'
                    )
        except Exception as e:
            logger.exception(f'Exception while validating/saving SubscriptionPlanForm: {e}')
        else:
            if form.errors:
                try:
                    logger.warning(f'SubscriptionPlanForm invalid: {form.errors.as_json()}' )
                except Exception:
                    logger.warning(f'SubscriptionPlanForm invalid: {form.errors}')
    else:
        form = SubscriptionPlanForm()

    return render(request, 'admin-user/create-subscription-plan.html', {'form': form, 'creating': True})


@staff_member_required
def admin_subscription_edit(request, pk):
    
    plan = get_object_or_404(SubscriptionPlan, pk=pk)

    if request.method == 'POST':
        form = SubscriptionPlanForm(request.POST, request.FILES, instance=plan)
        try:
            if form.is_valid():
                user_type = form.cleaned_data.get('user_type')
                is_active = form.cleaned_data.get('is_active')

                # If activating this plan, ensure no other active plan exists for same role
                if (
                    is_active and
                    SubscriptionPlan.objects.filter(
                        user_type=user_type,
                        is_active=True
                    ).exclude(pk=plan.pk).exists()
                ):
                    form.add_error(
                        None,
                        'Another active plan exists for this role. '
                        'Deactivate it before enabling this plan.'
                    )
                else:
                    form.save()
                    return redirect(
                        reverse('admin-subscriptions-list') + '?updated=1'
                    )
        except Exception as e:
            logger.exception(f'Exception while validating/saving SubscriptionPlanForm (edit): {e}')
        else:
            if form.errors:
                try:
                    logger.warning(f'SubscriptionPlanForm (edit) invalid: { form.errors.as_json()}')
                except Exception:
                    logger.warning(f'SubscriptionPlanForm (edit) invalid: {form.errors}')
    else:
        form = SubscriptionPlanForm(instance=plan)

    return render(request, 'admin-user/create-subscription-plan.html', {'form': form, 'creating': False, 'plan': plan})


@staff_member_required
@require_POST
def admin_subscription_delete(request, pk):
    
    plan = get_object_or_404(SubscriptionPlan, pk=pk)
    try:
        plan.delete()
        return JsonResponse({'status': 'success', 'message': 'Subscription plan deleted'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Failed to delete: {str(e)}'})


def contact_messages_list(request):
    # Get only non-deleted contact messages ordered by latest first
    contact_messages = ContactMessage.objects.filter(is_deleted=False).order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        contact_messages = contact_messages.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    # Filter functionality
    status_filter = request.GET.get('status', '')
    if status_filter:
        contact_messages = contact_messages.filter(status=status_filter)
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(contact_messages, 5)  # 10 records per page
    
    try:
        messages_page = paginator.page(page)
    except PageNotAnInteger:
        messages_page = paginator.page(1)
    except EmptyPage:
        messages_page = paginator.page(paginator.num_pages)
    
    context = {
        'contact_messages': messages_page,
        'paginator': paginator,
        'search_query': search_query,
        'status_filter': status_filter,
        'status_choices': ContactMessage.STATUS_CHOICES,
    }
    
    return render(request, 'contacts/contact_messages_list.html', context)


@csrf_exempt
def update_message_status(request, message_id):
    if request.method == 'POST':
        try:
            message = ContactMessage.objects.get(id=message_id)
            action = request.POST.get('action')
            
            if action == 'mark_read':
                message.status = 'read'
                message.save()
                
                return JsonResponse({
                    'status': 'success',
                    'message': f'Message marked as {message.get_status_display()}'
                })
            elif action == 'delete':
                # Soft delete
                message.is_deleted = True
                message.save()
                return JsonResponse({
                    'status': 'success',
                    'message': 'Message deleted successfully'
                })
            
        except ContactMessage.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Message not found'
            })
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request'
    })


def reply_to_message(request, message_id):
    message = get_object_or_404(ContactMessage, id=message_id)
    
    if request.method == 'POST':
        try:
            subject = request.POST.get('subject')
            reply_message = request.POST.get('message')
            attachment = request.FILES.get('attachment')

            # Prepare plain-text fallback and HTML content
            plain_text = strip_tags(reply_message)

            # Create multipart email with HTML alternative
            email = EmailMultiAlternatives(
                subject=subject,
                body=plain_text,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[message.email],
            )
            email.attach_alternative(reply_message, "text/html")

            # Add attachment if provided
            if attachment:
                email.attach(attachment.name, attachment.read(), attachment.content_type)

            # Send email
            email.send()
            
            # Update message status to replied
            message.status = 'replied'
            message.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Reply sent successfully!'
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Failed to send reply: {str(e)}'
            })
    
    context = {
        'message': message,
    }
    return render(request, 'contacts/reply_message.html', context)



def feedback_list(request):
    # Base queryset ordered by latest first
    feedbacks = Feedback.objects.all().order_by('-created_at')

    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        feedbacks = feedbacks.filter(
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query)
        )

    # Filters
    role_filter = request.GET.get('role', '')
    if role_filter:
        feedbacks = feedbacks.filter(role=role_filter)

    rating_filter = request.GET.get('rating', '')
    if rating_filter:
        feedbacks = feedbacks.filter(rate_us=rating_filter)

    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(feedbacks, 5)  # 5 per page

    try:
        feedback_page = paginator.page(page)
    except PageNotAnInteger:
        feedback_page = paginator.page(1)
    except EmptyPage:
        feedback_page = paginator.page(paginator.num_pages)

    context = {
        'feedbacks': feedback_page,
        'paginator': paginator,
        'search_query': search_query,
        'role_filter': role_filter,
        'rating_filter': rating_filter,
        'role_choices': Feedback.ROLE_CHOICES,
        'rating_choices': Feedback.RATING_CHOICES,
    }

    return render(request, 'contacts/feedback_list.html', context)


def feedback_detail(request, pk):
    feedback = get_object_or_404(Feedback, pk=pk)
    context = {'feedback': feedback}
    return render(request, 'contacts/feedback_detail.html', context)


def registered_patient_list_view(request):

    qs = CustomUser.objects.filter(user_type='patient').select_related('patient_profile').prefetch_related('subscriptions')

    # Filters from query params
    search_query = request.GET.get('search', '').strip()
    filter_deleted = request.GET.get('is_deleted', '')
    filter_subscription = request.GET.get('is_subscription', '')

    # Deleted filter
    if filter_deleted == '1':
        qs = qs.filter(is_deleted=True)
    elif filter_deleted == '0':
        qs = qs.filter(is_deleted=False)

    # Search across patient name, email, phone_number
    if search_query:
        qs = qs.filter(
            Q(patient_profile__full_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone_number__icontains=search_query)
        ).distinct()

    # Ordering - newest first
    qs = qs.order_by('-date_joined')

    # Pagination
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 10)
    try:
        per_page = int(per_page)
    except (TypeError, ValueError):
        per_page = 10

    paginator = Paginator(qs, per_page)
    try:
        patients = paginator.page(page)
    except PageNotAnInteger:
        patients = paginator.page(1)
    except EmptyPage:
        patients = paginator.page(paginator.num_pages)

    # Enhance each patient with subscription data for template and filter
    filtered_patients = []
    for patient in patients:
        sub_data = get_subscription_data(patient)
        patient.subscription_active = sub_data['subscription_active']
        patient.subscription_start = sub_data['subscription_start']
        patient.subscription_end = sub_data['subscription_end']
        
        # Apply subscription filter after fetching
        if filter_subscription == '1':
            if patient.subscription_active:
                filtered_patients.append(patient)
        elif filter_subscription == '0':
            if not patient.subscription_active:
                filtered_patients.append(patient)
        else:
            filtered_patients.append(patient)
    
    # Replace patients with filtered list if subscription filter is active
    if filter_subscription:
        patients.object_list = filtered_patients

    context = {
        'patients': patients,
        'paginator': paginator,
        'search_query': search_query,
        'filter_deleted': filter_deleted,
        'filter_subscription': filter_subscription,
        'per_page': per_page,
    }

    return render(request, 'admin-user/registered-patient-list.html', context)


def registered_hospital_list_view(request):

    qs = CustomUser.objects.filter(user_type='hospital').select_related('hospital_profile').prefetch_related('subscriptions')

    # Filters from query params
    search_query = request.GET.get('search', '').strip()
    filter_deleted = request.GET.get('is_deleted', '')
    filter_verified = request.GET.get('is_verified', '')
    filter_subscription = request.GET.get('is_subscription', '')

    # apply boolean filters only if explicitly set
    if filter_deleted == '1':
        qs = qs.filter(is_deleted=True)
    elif filter_deleted == '0':
        qs = qs.filter(is_deleted=False)

    if filter_verified == '1':
        qs = qs.filter(is_verified=True)
    elif filter_verified == '0':
        qs = qs.filter(is_verified=False)

    # Search across hospital name, email, phone_number
    if search_query:
        qs = qs.filter(
            Q(hospital_profile__name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone_number__icontains=search_query)
        ).distinct()

    # Ordering - newest first
    qs = qs.order_by('-date_joined')

    # Pagination
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 10)
    try:
        per_page = int(per_page)
    except (TypeError, ValueError):
        per_page = 10

    paginator = Paginator(qs, per_page)
    try:
        hospitals = paginator.page(page)
    except PageNotAnInteger:
        hospitals = paginator.page(1)
    except EmptyPage:
        hospitals = paginator.page(paginator.num_pages)

    # Enhance each hospital with subscription data for template and apply filter
    filtered_hospitals = []
    for hospital in hospitals:
        sub_data = get_subscription_data(hospital)
        hospital.subscription_active = sub_data['subscription_active']
        hospital.subscription_start = sub_data['subscription_start']
        hospital.subscription_end = sub_data['subscription_end']
        
        # Apply subscription filter after fetching
        if filter_subscription == '1':
            if hospital.subscription_active:
                filtered_hospitals.append(hospital)
        elif filter_subscription == '0':
            if not hospital.subscription_active:
                filtered_hospitals.append(hospital)
        else:
            filtered_hospitals.append(hospital)
    
    # Replace hospitals with filtered list if subscription filter is active
    if filter_subscription:
        hospitals.object_list = filtered_hospitals

    context = {
        'hospitals': hospitals,
        'paginator': paginator,
        'search_query': search_query,
        'filter_deleted': filter_deleted,
        'filter_verified': filter_verified,
        'filter_subscription': filter_subscription,
        'per_page': per_page,
    }

    return render(request, 'admin-user/registered-hospital-list.html', context)


def registered_doctor_list_view(request):

    qs = CustomUser.objects.filter(user_type='doctor').select_related('doctor_profile').prefetch_related(
        Prefetch('doctor_profile__specializations'), 'subscriptions'
    )

    # Filters from query params
    search_query = request.GET.get('search', '').strip()
    filter_deleted = request.GET.get('is_deleted', '')
    filter_verified = request.GET.get('is_verified', '')
    filter_subscription = request.GET.get('is_subscription', '')

    # apply boolean filters only if user explicitly set them

    if filter_deleted == '1':
        qs = qs.filter(is_deleted=True)
    elif filter_deleted == '0':
        qs = qs.filter(is_deleted=False)

    if filter_verified == '1':
        qs = qs.filter(is_verified=True)
    elif filter_verified == '0':
        qs = qs.filter(is_verified=False)

    # Search across doctor_name, email, phone_number, specializations
    if search_query:
        qs = qs.filter(
            Q(doctor_profile__doctor_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone_number__icontains=search_query) |
            Q(doctor_profile__specializations__name__icontains=search_query)
        ).distinct()

    # Ordering - newest first
    qs = qs.order_by('-date_joined')

    # Pagination
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 10)
    try:
        per_page = int(per_page)
    except (TypeError, ValueError):
        per_page = 10

    paginator = Paginator(qs, per_page)
    try:
        doctors = paginator.page(page)
    except PageNotAnInteger:
        doctors = paginator.page(1)
    except EmptyPage:
        doctors = paginator.page(paginator.num_pages)

    # Enhance each doctor with subscription data for template and apply filter
    filtered_doctors = []
    for doctor in doctors:
        sub_data = get_subscription_data(doctor)
        doctor.subscription_active = sub_data['subscription_active']
        doctor.subscription_start = sub_data['subscription_start']
        doctor.subscription_end = sub_data['subscription_end']
        
        # Apply subscription filter after fetching
        if filter_subscription == '1':
            if doctor.subscription_active:
                filtered_doctors.append(doctor)
        elif filter_subscription == '0':
            if not doctor.subscription_active:
                filtered_doctors.append(doctor)
        else:
            filtered_doctors.append(doctor)
    
    # Replace doctors with filtered list if subscription filter is active
    if filter_subscription:
        doctors.object_list = filtered_doctors

    context = {
        'doctors': doctors,
        'paginator': paginator,
        'search_query': search_query,
        'filter_deleted': filter_deleted,
        'filter_verified': filter_verified,
        'filter_subscription': filter_subscription,
        'per_page': per_page,
    }

    return render(request, 'admin-user/registered-doctors-list.html', context)




# --- AJAX endpoint to soft-delete / recover ---
@require_POST
def account_delete_or_recover_view(request, pk):
    """
    Admin can soft-delete or recover a user account.

    POST params:
        action: 'delete' or 'recover'

    Returns:
        JSON {status: 'success'|'error', message: '...'}
    """
    action = request.POST.get('action')
    if action not in ('delete', 'recover'):
        return HttpResponseBadRequest('Invalid action')

    user = get_object_or_404(CustomUser, pk=pk)

    if action == 'delete':
        if user.is_deleted:
            return JsonResponse({'status': 'error', 'message': 'Account already deleted.'})
        user.is_deleted = True
        user.is_active = False   # deactivate account when soft-deleted
        user.save(update_fields=['is_deleted', 'is_active'])
        return JsonResponse({'status': 'success', 'message': 'Account has been soft-deleted.'})

    elif action == 'recover':
        if not user.is_deleted:
            return JsonResponse({'status': 'error', 'message': 'Account is not deleted.'})
        user.is_deleted = False
        user.is_active = True   # reactivate account when recovered
        user.save(update_fields=['is_deleted', 'is_active'])
        return JsonResponse({'status': 'success', 'message': 'Account has been recovered and reactivated.'})


# ==================== Helper Function for Doctor Working Hours ====================

def get_doctor_profile(user):
    """
    Get doctor profile for any type of doctor (individual or hospital-associated)
    Returns DoctorProfile or raises DoesNotExist exception
    """
    # Works for both individual doctors and hospital-associated doctors
    # since both types have a OneToOne DoctorProfile relationship
    return user.doctor_profile


# ==================== Doctor Working Hours APIs ====================

@csrf_exempt
def get_doctor_working_hours(request):
    """
    GET: Fetch all 7 days of doctor's working hours
    If no working hours exist, return empty template for 7 days
    
    Returns:
    - working_hours: List of all 7 days with their status
    - mode: 'create' (no real data) or 'update' (has saved times)
    - has_data: Boolean indicating if any real working hours data exists
    """
    if request.method != 'GET':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
    
    if not request.user.is_authenticated or request.user.user_type != 'doctor':
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=401)
    
    try:
        doctor_profile = get_doctor_profile(request.user)
    except DoctorProfile.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Doctor profile not found'}, status=404)
    
    from .models import DoctorWorkingHours
    
    # Get or create all 7 days
    working_hours_list = []
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    for day_num in range(7):
        working_hour, created = DoctorWorkingHours.objects.get_or_create(
            doctor=doctor_profile,
            day_of_week=day_num,
            defaults={'is_off': False}
        )
        
        working_hours_list.append({
            'day_of_week': working_hour.day_of_week,
            'day_name': day_names[day_num],
            'start_time': working_hour.start_time.isoformat() if working_hour.start_time else None,
            'end_time': working_hour.end_time.isoformat() if working_hour.end_time else None,
            'is_off': working_hour.is_off,
        })
    
    # Check if any day has been modified (to determine if we're in create or update mode)
    # has_existing_data checks if any day is marked as off OR has actual times set
    has_existing_data = DoctorWorkingHours.objects.filter(doctor=doctor_profile).exclude(
        is_off=False, start_time__isnull=True, end_time__isnull=True
    ).exists()
    
    # has_real_data indicates if user has actually set working hours (not just auto-created empty records)
    has_real_data = DoctorWorkingHours.objects.filter(
        doctor=doctor_profile
    ).filter(
        Q(is_off=True) | Q(start_time__isnull=False) | Q(end_time__isnull=False)
    ).exists()
    
    return JsonResponse({
        'status': 'success',
        'mode': 'update' if has_existing_data else 'create',
        'has_data': has_real_data,  # Flag to indicate if any real data exists
        'working_hours': working_hours_list
    })


@csrf_exempt
def save_doctor_working_hours(request):
    """
    POST: Save/Update all 7 days of doctor's working hours
    Expects JSON with working_hours array containing all 7 days
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
    
    if not request.user.is_authenticated or request.user.user_type != 'doctor':
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=401)
    
    try:
        doctor_profile = get_doctor_profile(request.user)
    except DoctorProfile.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Doctor profile not found'}, status=404)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    
    working_hours_data = data.get('working_hours', [])
    
    # Validate all 7 days are present
    if len(working_hours_data) != 7:
        return JsonResponse({
            'status': 'error',
            'message': 'All 7 days must be provided'
        }, status=400)
    
    from .models import DoctorWorkingHours
    
    try:
        # Validate each day's data
        errors = []
        for idx, day_data in enumerate(working_hours_data):
            day_num = day_data.get('day_of_week')
            is_off = day_data.get('is_off', False)
            start_time = day_data.get('start_time')
            end_time = day_data.get('end_time')
            
            # Validate day_of_week
            if day_num not in range(7):
                errors.append(f"Day {idx}: Invalid day of week")
                continue
            
            # If not off, validate times
            if not is_off:
                if not start_time or not end_time:
                    errors.append(f"Day {idx} ({['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][day_num]}): Start and End times required")
                    continue
                
                # Compare times
                try:
                    start = dt_time.fromisoformat(start_time)
                    end = dt_time.fromisoformat(end_time)
                    if start >= end:
                        errors.append(f"Day {idx} ({['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][day_num]}): Start time must be before End time")
                except (ValueError, AttributeError):
                    errors.append(f"Day {idx}: Invalid time format")
        
        if errors:
            return JsonResponse({
                'status': 'error',
                'message': 'Validation failed',
                'errors': errors
            }, status=400)
        
        # Save working hours for all days
        for day_data in working_hours_data:
            day_num = day_data.get('day_of_week')
            is_off = day_data.get('is_off', False)
            start_time_str = day_data.get('start_time') if not is_off else None
            end_time_str = day_data.get('end_time') if not is_off else None
            
            working_hour, created = DoctorWorkingHours.objects.get_or_create(
                doctor=doctor_profile,
                day_of_week=day_num
            )
            
            working_hour.is_off = is_off
            working_hour.start_time = start_time_str
            working_hour.end_time = end_time_str
            working_hour.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Working hours saved successfully'
        })
    
    except Exception as e:
        logger.error(f"Error saving working hours: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'An error occurred while saving working hours'
        }, status=500)


# ==================== Hospital Dashboard ====================

def hospital_dashboard(request):
    """
    Hospital Dashboard - displays account info, availability, subscription status, and pending appointments
    Shows appointments for: direct hospital bookings + bookings with associated doctors
    """
    if not request.user.is_authenticated or request.user.user_type != 'hospital':
        return redirect('login')
    
    try:
        hospital_profile = request.user.hospital_profile
    except HospitalClinicProfile.DoesNotExist:
        return redirect('login')
    
    # Get latest subscription (ordered by creation date to get most recent request)
    latest_subscription = request.user.subscriptions.filter(
        subscription_plan__user_type='hospital'
    ).order_by('-created_at').first()
    
    logger.info(f"Hospital Dashboard - User: {request.user.email}, Subscription: {latest_subscription}")
    
    # Calculate subscription status and related data
    days_until_expiry = None
    subscription_status = None
    show_no_plan_alert = False
    can_buy_plan = False
    
    if latest_subscription:
        from django.utils import timezone
        today = timezone.now().date()
        end_date = latest_subscription.end_date
        start_date = latest_subscription.start_date
        days_diff = (end_date - today).days
        
        # Determine status based on is_active flag and dates
        if not latest_subscription.is_active:
            # Subscription not yet activated by admin
            if latest_subscription.status == 'pending':
                subscription_status = 'pending_verification'
                logger.info("Subscription pending admin verification")
            elif latest_subscription.status == 'rejected':
                subscription_status = 'rejected'
                can_buy_plan = True
                show_no_plan_alert = True
                logger.info("Subscription rejected by admin")
            else:
                subscription_status = 'inactive'
                show_no_plan_alert = True
                can_buy_plan = True
        elif start_date > today:
            # Future subscription (active but not started yet)
            subscription_status = 'future'
            logger.info(f"Future subscription starting on {start_date}")
        elif days_diff < 0:
            # Expired
            days_until_expiry = abs(days_diff)
            subscription_status = 'expired'
            show_no_plan_alert = True
            can_buy_plan = True
            logger.info(f"Subscription expired {days_until_expiry} days ago")
        elif days_diff == 0:
            # Expires today
            days_until_expiry = 0
            subscription_status = 'expires_today'
            logger.info("Subscription expires today")
        elif days_diff <= 7:
            # Expiring within 7 days
            days_until_expiry = days_diff
            subscription_status = 'expiring_soon'
            logger.warning(f"Subscription expiring in {days_until_expiry} days")
        else:
            # Active and not expiring soon
            days_until_expiry = days_diff
            subscription_status = 'active'
            logger.info(f"Subscription active, expires in {days_until_expiry} days")
    else:
        # No subscription at all
        subscription_status = 'none'
        show_no_plan_alert = True
        can_buy_plan = True
        logger.info("No subscription found for hospital")
    
    # Get verified associated doctors for filter dropdown
    associated_doctors = HospitalDoctors.objects.filter(
        hospital=hospital_profile,
        is_active=True,
        doctor__user__is_verified=True
    ).select_related('doctor', 'doctor__user').order_by('doctor__doctor_name')
    
    # Get pending appointments with filters
    filter_date = request.GET.get('pendingAppointmentsDateFilter')
    filter_doctor_id = request.GET.get('pendingAppointmentsDoctorFilter')
    
    from django.utils import timezone
    from django.db.models import Q
    today = timezone.now().date()
    
    # Build query: appointments for hospital OR associated doctors
    doctor_ids = [hd.doctor.id for hd in associated_doctors]
    
    pending_appointments_qs = Appointment.objects.filter(
        Q(hospital=hospital_profile) | Q(doctor_id__in=doctor_ids),
        status='PENDING'
    )
    
    # Apply date filter (default to today if no filter)
    if filter_date:
        pending_appointments_qs = pending_appointments_qs.filter(appointment_date=filter_date)
    else:
        pending_appointments_qs = pending_appointments_qs.filter(appointment_date=today)
    
    # Apply doctor filter if specified
    if filter_doctor_id:
        try:
            pending_appointments_qs = pending_appointments_qs.filter(doctor_id=int(filter_doctor_id))
        except (ValueError, TypeError):
            pass
    
    pending_appointments = pending_appointments_qs.select_related(
        'patient__user', 'doctor', 'hospital'
    ).order_by('-created_at')
    
    context = {
        'hospital': hospital_profile,
        'user': request.user,
        'subscription': latest_subscription,
        'days_until_expiry': days_until_expiry,
        'subscription_status': subscription_status,
        'show_no_plan_alert': show_no_plan_alert,
        'can_buy_plan': can_buy_plan,
        'pending_appointments': pending_appointments,
        'pending_count': pending_appointments.count(),
        'filter_date': filter_date,
        'filter_doctor_id': filter_doctor_id,
        'associated_doctors': associated_doctors,
        'today': today,
    }
    
    logger.debug(f"Hospital Dashboard Context - Status: {subscription_status}, Days: {days_until_expiry}, Show Alert: {show_no_plan_alert}")
    
    return render(request, 'accounts/hospital-dashboard.html', context)


@csrf_exempt
def toggle_hospital_availability(request):
    """
    AJAX endpoint to toggle hospital availability (Open/Closed)
    """
    if not request.user.is_authenticated or request.user.user_type != 'hospital':
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        from django.utils import timezone
        hospital_profile = request.user.hospital_profile
        hospital_profile.is_available = not hospital_profile.is_available
        hospital_profile.availability_last_updated = timezone.now()
        hospital_profile.save(update_fields=['is_available', 'availability_last_updated'])
        
        return JsonResponse({
            'status': 'success',
            'is_available': hospital_profile.is_available,
            'last_updated': hospital_profile.availability_last_updated.isoformat(),
            'message': 'Hospital status updated successfully'
        })
    except Exception as e:
        logger.error(f"Error toggling hospital availability: {str(e)}")
        return JsonResponse({'error': 'Failed to update availability'}, status=500)


@csrf_exempt
def get_hospital_working_hours(request):
    """
    Get hospital working hours for all days of the week
    Returns existing hours or default structure if none exist
    """
    if not request.user.is_authenticated or request.user.user_type != 'hospital':
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    try:
        from .models import HospitalWorkingHours
        hospital_profile = request.user.hospital_profile
        
        # Get all working hours for this hospital
        working_hours = HospitalWorkingHours.objects.filter(
            hospital=hospital_profile
        ).order_by('day_of_week')
        
        # If no working hours exist, create default structure
        if not working_hours.exists():
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            data = []
            for day_num in range(7):
                data.append({
                    'day_of_week': day_num,
                    'day_name': day_names[day_num],
                    'start_time': None,
                    'end_time': None,
                    'is_off': False
                })
            
            return JsonResponse({
                'status': 'success',
                'working_hours': data,
                'mode': 'create'
            })
        
        # Build response with existing data
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        data = []
        for wh in working_hours:
            data.append({
                'day_of_week': wh.day_of_week,
                'day_name': day_names[wh.day_of_week],
                'start_time': wh.start_time.strftime('%H:%M') if wh.start_time else None,
                'end_time': wh.end_time.strftime('%H:%M') if wh.end_time else None,
                'is_off': wh.is_off
            })
        
        return JsonResponse({
            'status': 'success',
            'working_hours': data,
            'mode': 'update'
        })
        
    except Exception as e:
        logger.error(f"Error fetching hospital working hours: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'Failed to fetch working hours'
        }, status=500)


@csrf_exempt
def save_hospital_working_hours(request):
    """
    Save or update hospital working hours for all days
    Expects JSON data with working hours for all 7 days
    """
    if not request.user.is_authenticated or request.user.user_type != 'hospital':
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        from .models import HospitalWorkingHours
        import json
        
        hospital_profile = request.user.hospital_profile
        data = json.loads(request.body)
        working_hours_data = data.get('working_hours', [])
        
        if not working_hours_data or len(working_hours_data) != 7:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid working hours data. Must include all 7 days.'
            }, status=400)
        
        # Validate and save each day
        saved_hours = []
        for day_data in working_hours_data:
            day_of_week = day_data.get('day_of_week')
            start_time = day_data.get('start_time')
            end_time = day_data.get('end_time')
            is_off = day_data.get('is_off', False)
            
            # Validate day_of_week
            if day_of_week is None or not (0 <= day_of_week <= 6):
                return JsonResponse({
                    'status': 'error',
                    'message': f'Invalid day_of_week: {day_of_week}'
                }, status=400)
            
            # If day is not off, validate times
            if not is_off:
                if not start_time or not end_time:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Start and end times required for working days'
                    }, status=400)
                
                # Convert to time objects for validation
                from datetime import datetime
                try:
                    start_obj = datetime.strptime(start_time, '%H:%M').time()
                    end_obj = datetime.strptime(end_time, '%H:%M').time()
                    
                    if start_obj >= end_obj:
                        return JsonResponse({
                            'status': 'error',
                            'message': f'End time must be after start time'
                        }, status=400)
                except ValueError:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Invalid time format'
                    }, status=400)
            else:
                # Day is off, clear times
                start_time = None
                end_time = None
            
            # Update or create working hours
            wh, created = HospitalWorkingHours.objects.update_or_create(
                hospital=hospital_profile,
                day_of_week=day_of_week,
                defaults={
                    'start_time': start_time,
                    'end_time': end_time,
                    'is_off': is_off
                }
            )
            saved_hours.append(wh)
        
        logger.info(f"Hospital working hours saved for hospital ID {hospital_profile.id}")
        
        return JsonResponse({
            'status': 'success',
            'message': 'Working hours saved successfully'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Error saving hospital working hours: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'An error occurred while saving working hours'
        }, status=500)


class HospitalBookingsExportAPIView(APIView):
    """
    Export hospital bookings as CSV
    Includes: direct hospital bookings + bookings with associated doctors
    """
    def get(self, request):
        if not request.user.is_authenticated or request.user.user_type != 'hospital':
            return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            hospital_profile = request.user.hospital_profile
            status_param = request.GET.get('status', '').lower()
            
            if status_param not in ['accepted', 'rejected']:
                return Response({
                    'error': 'Invalid status. Must be "accepted" or "rejected"'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Map to database status values
            status_map = {'accepted': 'ACCEPTED', 'rejected': 'REJECTED'}
            booking_status = status_map[status_param]
            
            # Get associated doctor IDs
            from django.db.models import Q
            associated_doctor_ids = HospitalDoctors.objects.filter(
                hospital=hospital_profile,
                is_active=True,
                doctor__user__is_verified=True
            ).values_list('doctor_id', flat=True)
            
            # Query appointments: direct hospital bookings + associated doctors' bookings
            appointments = Appointment.objects.filter(
                Q(hospital=hospital_profile) | Q(doctor_id__in=associated_doctor_ids),
                status=booking_status
            ).select_related('patient__user', 'doctor', 'hospital').order_by('-appointment_date')
            
            # Create CSV
            import csv
            from django.http import HttpResponse
            from io import StringIO
            
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{booking_status.lower()}_bookings_{hospital_profile.name}_{timezone.now().date()}.csv"'
            
            writer = csv.writer(response)
            
            # Write header
            writer.writerow([
                'Appointment ID',
                'Patient Name',
                'Patient Email',
                'Patient Phone',
                'Booking Type',
                'Doctor Name',
                'Hospital Name',
                'Appointment Date',
                'Status',
                'Booked On',
                'Patient Message',
                'Doctor Provided Time' if booking_status == 'ACCEPTED' else 'Rejection Reason'
            ])
            
            # Write data rows
            for appt in appointments:
                booking_type = 'Hospital Booking' if appt.hospital else 'Doctor Booking'
                doctor_name = appt.doctor.doctor_name if appt.doctor else 'N/A'
                hospital_name = appt.hospital.name if appt.hospital else (
                    hospital_profile.name if appt.doctor and appt.doctor.id in associated_doctor_ids else 'N/A'
                )
                
                writer.writerow([
                    appt.id,
                    appt.patient.full_name,
                    appt.patient.user.email,
                    appt.patient.user.phone_number or 'N/A',
                    booking_type,
                    doctor_name,
                    hospital_name,
                    appt.appointment_date.strftime('%Y-%m-%d'),
                    appt.get_status_display(),
                    appt.created_at.strftime('%Y-%m-%d %H:%M'),
                    appt.patient_message or 'N/A',
                    appt.doctor_provided_time.strftime('%H:%M') if booking_status == 'ACCEPTED' and appt.doctor_provided_time else (
                        appt.rejection_reason if booking_status == 'REJECTED' else 'N/A'
                    )
                ])
            
            return response
            
        except Exception as e:
            logger.error(f"Error exporting hospital bookings: {str(e)}")
            return Response({
                'error': 'Failed to export bookings'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== Appointment Booking System ====================

from .models import Appointment
from .serializers import (
    AppointmentCreateSerializer, 
    AppointmentListSerializer,
    AppointmentAcceptSerializer,
    AppointmentRejectSerializer,
    AppointmentCancelSerializer
)


class AppointmentCreateAPIView(APIView):
    """
    API for patients to create new appointments
    POST /api/appointments/create/
    """
    def post(self, request):
        try:
            # Check if user is authenticated
            if not request.user.is_authenticated:
                return Response({
                    'error': 'Please log in with your valid account first.'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Check if user is a patient
            if request.user.user_type != 'patient':
                return Response({
                    'error': 'Only patients can create appointments'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Check if user is verified
            if not request.user.is_verified:
                return Response({
                    'error': 'Your account must be verified to book appointments'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Validate and create appointment
            serializer = AppointmentCreateSerializer(
                data=request.data,
                context={'request': request}
            )
            
            if serializer.is_valid():
                appointment = serializer.save()
                response_serializer = AppointmentListSerializer(appointment)
                
                logger.info(f"Appointment created: ID {appointment.id} by patient {request.user.email}")
                
                return Response({
                    'message': 'Appointment created successfully',
                    'appointment': response_serializer.data,
                    'status': 'success'
                }, status=status.HTTP_201_CREATED)
            
            return Response({
                'errors': serializer.errors,
                'status': 'error'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error creating appointment: {str(e)}")
            return Response({
                'error': 'An error occurred while creating the appointment',
                'status': 'error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AppointmentListAPIView(APIView):
    """
    API to list appointments
    GET /api/appointments/list/
    - For patients: returns their appointments
    - For doctors: returns appointments with optional status filter
    """
    def get(self, request):
        try:
            if not request.user.is_authenticated:
                return Response({
                    'error': 'Please log in with your valid account first.'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            user_type = request.user.user_type
            status_filter = request.GET.get('status', '')
            
            if user_type == 'patient':
                # Get patient's appointments
                try:
                    patient = request.user.patient_profile
                    appointments = Appointment.objects.filter(
                        patient=patient
                    ).select_related('doctor__user').prefetch_related('doctor__specializations')
                    
                    if status_filter:
                        appointments = appointments.filter(status=status_filter.upper())
                    
                except PatientProfile.DoesNotExist:
                    return Response({
                        'error': 'Patient profile not found'
                    }, status=status.HTTP_404_NOT_FOUND)
            
            elif user_type == 'doctor':
                # Get doctor's appointments
                try:
                    doctor = request.user.doctor_profile
                    appointments = Appointment.objects.filter(
                        doctor=doctor
                    ).select_related('patient__user')
                    
                    if status_filter:
                        appointments = appointments.filter(status=status_filter.upper())
                    
                except DoctorProfile.DoesNotExist:
                    return Response({
                        'error': 'Doctor profile not found'
                    }, status=status.HTTP_404_NOT_FOUND)
            
            else:
                return Response({
                    'error': 'Invalid user type'
                }, status=status.HTTP_403_FORBIDDEN)
            
            serializer = AppointmentListSerializer(appointments, many=True)
            
            return Response({
                'appointments': serializer.data,
                'total_count': appointments.count(),
                'status': 'success'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error listing appointments: {str(e)}")
            return Response({
                'error': 'An error occurred while fetching appointments',
                'status': 'error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AppointmentAcceptAPIView(APIView):
    """
    API for doctors and hospitals to accept appointments
    POST /api/appointments/<id>/accept/
    """
    def post(self, request, appointment_id):
        try:
            if not request.user.is_authenticated:
                return Response({
                    'error': 'Please log in with your valid account first.'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            if request.user.user_type not in ['doctor', 'hospital']:
                return Response({
                    'error': 'Only doctors and hospitals can accept appointments'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Handle doctor user
            if request.user.user_type == 'doctor':
                try:
                    doctor = request.user.doctor_profile
                except DoctorProfile.DoesNotExist:
                    return Response({
                        'error': 'Doctor profile not found'
                    }, status=status.HTTP_404_NOT_FOUND)
                
                # Get appointment for this doctor
                try:
                    appointment = Appointment.objects.get(id=appointment_id, doctor=doctor)
                except Appointment.DoesNotExist:
                    return Response({
                        'error': 'Appointment not found'
                    }, status=status.HTTP_404_NOT_FOUND)
            
            # Handle hospital user
            elif request.user.user_type == 'hospital':
                try:
                    hospital = request.user.hospital_profile
                except HospitalClinicProfile.DoesNotExist:
                    return Response({
                        'error': 'Hospital profile not found'
                    }, status=status.HTTP_404_NOT_FOUND)
                
                # Get associated doctor IDs
                from django.db.models import Q
                associated_doctor_ids = HospitalDoctors.objects.filter(
                    hospital=hospital,
                    is_active=True
                ).values_list('doctor_id', flat=True)
                
                # Get appointment for hospital or associated doctors
                try:
                    appointment = Appointment.objects.get(
                        Q(id=appointment_id),
                        Q(hospital=hospital) | Q(doctor_id__in=associated_doctor_ids)
                    )
                except Appointment.DoesNotExist:
                    return Response({
                        'error': 'Appointment not found or you do not have permission to manage it'
                    }, status=status.HTTP_404_NOT_FOUND)
            
            # Validate
            serializer = AppointmentAcceptSerializer(
                data=request.data,
                context={'appointment': appointment}
            )
            
            if serializer.is_valid():
                # Update appointment
                appointment.status = 'ACCEPTED'
                appointment.doctor_provided_time = serializer.validated_data['doctor_provided_time']
                appointment.save()
                
                response_serializer = AppointmentListSerializer(appointment)
                
                user_role = 'doctor' if request.user.user_type == 'doctor' else 'hospital'
                logger.info(f"Appointment {appointment_id} accepted by {user_role} {request.user.email}")
                
                return Response({
                    'message': 'Appointment accepted successfully',
                    'appointment': response_serializer.data,
                    'status': 'success'
                }, status=status.HTTP_200_OK)
            
            return Response({
                'errors': serializer.errors,
                'status': 'error'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error accepting appointment: {str(e)}")
            return Response({
                'error': 'An error occurred while accepting the appointment',
                'status': 'error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AppointmentRejectAPIView(APIView):
    """
    API for doctors and hospitals to reject appointments
    POST /api/appointments/<id>/reject/
    """
    def post(self, request, appointment_id):
        try:
            if not request.user.is_authenticated:
                return Response({
                    'error': 'Please log in with your valid account first.'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            if request.user.user_type not in ['doctor', 'hospital']:
                return Response({
                    'error': 'Only doctors and hospitals can reject appointments'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Handle doctor user
            if request.user.user_type == 'doctor':
                try:
                    doctor = request.user.doctor_profile
                except DoctorProfile.DoesNotExist:
                    return Response({
                        'error': 'Doctor profile not found'
                    }, status=status.HTTP_404_NOT_FOUND)
                
                # Get appointment for this doctor
                try:
                    appointment = Appointment.objects.get(id=appointment_id, doctor=doctor)
                except Appointment.DoesNotExist:
                    return Response({
                        'error': 'Appointment not found'
                    }, status=status.HTTP_404_NOT_FOUND)
            
            # Handle hospital user
            elif request.user.user_type == 'hospital':
                try:
                    hospital = request.user.hospital_profile
                except HospitalClinicProfile.DoesNotExist:
                    return Response({
                        'error': 'Hospital profile not found'
                    }, status=status.HTTP_404_NOT_FOUND)
                
                # Get associated doctor IDs
                from django.db.models import Q
                associated_doctor_ids = HospitalDoctors.objects.filter(
                    hospital=hospital,
                    is_active=True
                ).values_list('doctor_id', flat=True)
                
                # Get appointment for hospital or associated doctors
                try:
                    appointment = Appointment.objects.get(
                        Q(id=appointment_id),
                        Q(hospital=hospital) | Q(doctor_id__in=associated_doctor_ids)
                    )
                except Appointment.DoesNotExist:
                    return Response({
                        'error': 'Appointment not found or you do not have permission to manage it'
                    }, status=status.HTTP_404_NOT_FOUND)
            
            # Validate
            serializer = AppointmentRejectSerializer(
                data=request.data,
                context={'appointment': appointment}
            )
            
            if serializer.is_valid():
                # Update appointment
                appointment.status = 'REJECTED'
                appointment.rejection_reason = serializer.validated_data['rejection_reason']
                appointment.save()
                
                response_serializer = AppointmentListSerializer(appointment)
                
                user_role = 'doctor' if request.user.user_type == 'doctor' else 'hospital'
                logger.info(f"Appointment {appointment_id} rejected by {user_role} {request.user.email}")
                
                return Response({
                    'message': 'Appointment rejected successfully',
                    'appointment': response_serializer.data,
                    'status': 'success'
                }, status=status.HTTP_200_OK)
            
            return Response({
                'errors': serializer.errors,
                'status': 'error'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error rejecting appointment: {str(e)}")
            return Response({
                'error': 'An error occurred while rejecting the appointment',
                'status': 'error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AppointmentCancelAPIView(APIView):
    """
    API for patients to cancel appointments
    POST /api/appointments/<id>/cancel/
    """
    def post(self, request, appointment_id):
        try:
            if not request.user.is_authenticated:
                return Response({
                    'error': 'Please log in with your valid account first.'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            if request.user.user_type != 'patient':
                return Response({
                    'error': 'Only patients can cancel appointments'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get patient profile
            try:
                patient = request.user.patient_profile
            except PatientProfile.DoesNotExist:
                return Response({
                    'error': 'Patient profile not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Get appointment
            try:
                appointment = Appointment.objects.get(id=appointment_id, patient=patient)
            except Appointment.DoesNotExist:
                return Response({
                    'error': 'Appointment not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Validate
            serializer = AppointmentCancelSerializer(
                data=request.data,
                context={'appointment': appointment}
            )
            
            if serializer.is_valid():
                # Update appointment
                appointment.status = 'CANCELED'
                appointment.cancellation_reason = serializer.validated_data['cancellation_reason']
                appointment.save()
                
                response_serializer = AppointmentListSerializer(appointment)
                
                logger.info(f"Appointment {appointment_id} canceled by patient {request.user.email}")
                
                return Response({
                    'message': 'Appointment canceled successfully',
                    'appointment': response_serializer.data,
                    'status': 'success'
                }, status=status.HTTP_200_OK)
            
            return Response({
                'errors': serializer.errors,
                'status': 'error'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error canceling appointment: {str(e)}")
            return Response({
                'error': 'An error occurred while canceling the appointment',
                'status': 'error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@require_POST
def get_pending_appointments_count(request):
    """
    Get count of pending appointments for doctor dashboard
    """
    try:
        if not request.user.is_authenticated or request.user.user_type != 'doctor':
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        doctor = request.user.doctor_profile
        count = Appointment.objects.filter(doctor=doctor, status='PENDING').count()
        
        return JsonResponse({
            'count': count,
            'status': 'success'
        })
    except Exception as e:
        logger.error(f"Error getting pending appointments count: {str(e)}")
        return JsonResponse({
            'error': 'An error occurred',
            'status': 'error'
        }, status=500)


# ==================== Subscription Management ====================

def subscription_request_page(request):
    """
    Display subscription request page with stepper form
    Only for doctors who don't have an active or pending subscription
    """
    if not request.user.is_authenticated or request.user.user_type != 'doctor':
        return redirect('login')
    
    try:
        doctor_profile = request.user.doctor_profile
    except DoctorProfile.DoesNotExist:
        return redirect('login')
    
    # Check if user already has an active or pending subscription
    from django.utils import timezone
    today = timezone.now().date()
    
    existing_subscription = request.user.subscriptions.filter(
        subscription_plan__user_type='doctor'
    ).order_by('-created_at').first()
    
    if existing_subscription:
        # Check if active (admin approved and within date range)
        if existing_subscription.is_active and existing_subscription.start_date <= today <= existing_subscription.end_date:
            # Already have active subscription
            return redirect('doctor-dashboard')
        
        # Check if pending (not yet approved by admin)
        if not existing_subscription.is_active and existing_subscription.status == 'pending':
            # Already have pending request
            return redirect('doctor-dashboard')
    
    # Get the subscription plan for doctors
    try:
        plan = SubscriptionPlan.objects.filter(user_type='doctor', is_active=True).first()
        if not plan:
            # No plan available
            return render(request, 'accounts/subscription-error.html', {
                'error_message': 'No subscription plans are currently available. Please contact admin.'
            })
    except SubscriptionPlan.DoesNotExist:
        return render(request, 'accounts/subscription-error.html', {
            'error_message': 'No subscription plans found. Please contact admin.'
        })
    
    context = {
        'plan': plan,
        'user': request.user,
        'user_full_name': doctor_profile.doctor_name,
    }
    
    return render(request, 'accounts/subscription-request.html', context)


@csrf_exempt
@require_POST
def subscription_request_submit(request):
    """
    Handle subscription request form submission
    """
    if not request.user.is_authenticated or request.user.user_type != 'doctor':
        return JsonResponse({'error': 'Unauthorized', 'status': 'error'}, status=401)
    
    try:
        # Check for existing active or pending subscription
        from django.utils import timezone
        today = timezone.now().date()
        
        existing_subscription = request.user.subscriptions.filter(
            subscription_plan__user_type='doctor'
        ).order_by('-created_at').first()
        
        if existing_subscription:
            if existing_subscription.is_active and existing_subscription.start_date <= today <= existing_subscription.end_date:
                return JsonResponse({
                    'status': 'error',
                    'message': 'You already have an active subscription'
                }, status=400)
            
            if not existing_subscription.is_active and existing_subscription.status == 'pending':
                return JsonResponse({
                    'status': 'error',
                    'message': 'You already have a pending subscription request'
                }, status=400)
        
        # Get form data
        plan_id = request.POST.get('plan_id')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        duration_months = request.POST.get('duration_months')
        final_amount = request.POST.get('final_amount')
        payment_screenshot = request.FILES.get('payment_screenshot')
        payment_message = request.POST.get('payment_message', '')
        
        # Validate required fields
        if not all([plan_id, start_date, end_date, duration_months, final_amount, payment_screenshot]):
            return JsonResponse({
                'status': 'error',
                'message': 'All fields are required'
            }, status=400)
        
        # Get subscription plan
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id, user_type='doctor', is_active=True)
        except SubscriptionPlan.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid subscription plan'
            }, status=400)
        
        # Validate dates
        from datetime import datetime
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid date format'
            }, status=400)
        
        if start_date_obj < today:
            return JsonResponse({
                'status': 'error',
                'message': 'Start date cannot be in the past'
            }, status=400)
        
        # Create subscription request
        subscription = UserSubscription.objects.create(
            user=request.user,
            subscription_plan=plan,
            start_date=start_date_obj,
            end_date=end_date_obj,
            duration_in_months=int(duration_months),
            final_amount_paid=int(final_amount),
            payment_screenshot=payment_screenshot,
            payment_message=payment_message,
            is_active=False,  # Admin will activate after verification
            status='pending'
        )
        
        logger.info(f"Subscription request created: ID={subscription.id}, User={request.user.email}")
        
        return JsonResponse({
            'status': 'success',
            'message': 'Subscription request submitted successfully',
            'subscription_id': subscription.id
        })
        
    except Exception as e:
        logger.error(f"Error submitting subscription request: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'An error occurred while processing your request'
        }, status=500)


# ==================== Hospital Subscription Management ====================

def hospital_subscription_request_page(request):
    """
    Display subscription request page with stepper form for hospitals
    Only for hospitals who don't have an active or pending subscription
    """
    if not request.user.is_authenticated or request.user.user_type != 'hospital':
        return redirect('login')
    
    try:
        hospital_profile = request.user.hospital_profile
    except HospitalClinicProfile.DoesNotExist:
        return redirect('login')
    
    # Check if user already has an active or pending subscription
    from django.utils import timezone
    today = timezone.now().date()
    
    existing_subscription = request.user.subscriptions.filter(
        subscription_plan__user_type='hospital'
    ).order_by('-created_at').first()
    
    if existing_subscription:
        # Check if active (admin approved and within date range)
        if existing_subscription.is_active and existing_subscription.start_date <= today <= existing_subscription.end_date:
            # Already have active subscription
            return redirect('hospital-dashboard')
        
        # Check if pending (not yet approved by admin)
        if not existing_subscription.is_active and existing_subscription.status == 'pending':
            # Already have pending request
            return redirect('hospital-dashboard')
    
    # Get the subscription plan for hospitals
    try:
        plan = SubscriptionPlan.objects.filter(user_type='hospital', is_active=True).first()
        if not plan:
            # No plan available
            return render(request, 'accounts/subscription-error.html', {
                'error_message': 'No subscription plans are currently available. Please contact admin.'
            })
    except SubscriptionPlan.DoesNotExist:
        return render(request, 'accounts/subscription-error.html', {
            'error_message': 'No subscription plans found. Please contact admin.'
        })
    
    context = {
        'plan': plan,
        'user': request.user,
        'user_full_name': hospital_profile.name,
    }
    
    return render(request, 'accounts/hospital-subscription-request.html', context)


@csrf_exempt
@require_POST
def hospital_subscription_request_submit(request):
    """
    Handle hospital subscription request form submission
    """
    if not request.user.is_authenticated or request.user.user_type != 'hospital':
        return JsonResponse({'error': 'Unauthorized', 'status': 'error'}, status=401)
    
    try:
        # Check for existing active or pending subscription
        from django.utils import timezone
        today = timezone.now().date()
        
        existing_subscription = request.user.subscriptions.filter(
            subscription_plan__user_type='hospital'
        ).order_by('-created_at').first()
        
        if existing_subscription:
            if existing_subscription.is_active and existing_subscription.start_date <= today <= existing_subscription.end_date:
                return JsonResponse({
                    'status': 'error',
                    'message': 'You already have an active subscription'
                }, status=400)
            
            if not existing_subscription.is_active and existing_subscription.status == 'pending':
                return JsonResponse({
                    'status': 'error',
                    'message': 'You already have a pending subscription request'
                }, status=400)
        
        # Get form data
        plan_id = request.POST.get('plan_id')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        duration_months = request.POST.get('duration_months')
        final_amount = request.POST.get('final_amount')
        payment_screenshot = request.FILES.get('payment_screenshot')
        payment_message = request.POST.get('payment_message', '')
        
        # Validate required fields
        if not all([plan_id, start_date, end_date, duration_months, final_amount, payment_screenshot]):
            return JsonResponse({
                'status': 'error',
                'message': 'All fields are required'
            }, status=400)
        
        # Get subscription plan
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id, user_type='hospital', is_active=True)
        except SubscriptionPlan.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid subscription plan'
            }, status=400)
        
        # Validate dates
        from datetime import datetime
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid date format'
            }, status=400)
        
        if start_date_obj < today:
            return JsonResponse({
                'status': 'error',
                'message': 'Start date cannot be in the past'
            }, status=400)
        
        # Create subscription request
        subscription = UserSubscription.objects.create(
            user=request.user,
            subscription_plan=plan,
            start_date=start_date_obj,
            end_date=end_date_obj,
            duration_in_months=int(duration_months),
            final_amount_paid=int(final_amount),
            payment_screenshot=payment_screenshot,
            payment_message=payment_message,
            is_active=False,  # Admin will activate after verification
            status='pending'
        )
        
        logger.info(f"Hospital subscription request created: ID={subscription.id}, User={request.user.email}")
        
        return JsonResponse({
            'status': 'success',
            'message': 'Subscription request submitted successfully',
            'subscription_id': subscription.id
        })
        
    except Exception as e:
        logger.error(f"Error submitting hospital subscription request: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'An error occurred while processing your request'
        }, status=500)


def patient_subscription_request_page(request):
    """
    Display subscription request page with stepper form for patients
    Only for patients who don't have an active or pending subscription
    """
    if not request.user.is_authenticated or request.user.user_type != 'patient':
        return redirect('login')
    
    try:
        patient_profile = request.user.patient_profile
    except PatientProfile.DoesNotExist:
        return redirect('login')
    
    # Check if user already has an active or pending subscription
    from django.utils import timezone
    today = timezone.now().date()
    
    existing_subscription = request.user.subscriptions.filter(
        subscription_plan__user_type='patient'
    ).order_by('-created_at').first()
    
    if existing_subscription:
        # Check if active (admin approved and within date range)
        if existing_subscription.is_active and existing_subscription.start_date <= today <= existing_subscription.end_date:
            # Already have active subscription
            return redirect('patient-dashboard')
        
        # Check if pending (not yet approved by admin)
        if not existing_subscription.is_active and existing_subscription.status == 'pending':
            # Already have pending request
            return redirect('patient-dashboard')
    
    # Get the subscription plan for patients
    try:
        plan = SubscriptionPlan.objects.filter(user_type='patient', is_active=True).first()
        if not plan:
            # No plan available
            return render(request, 'accounts/subscription-error.html', {
                'error_message': 'No subscription plans are currently available. Please contact admin.'
            })
    except SubscriptionPlan.DoesNotExist:
        return render(request, 'accounts/subscription-error.html', {
            'error_message': 'No subscription plans found. Please contact admin.'
        })
    
    context = {
        'plan': plan,
        'user': request.user,
        'user_full_name': patient_profile.full_name,
    }
    
    return render(request, 'accounts/patient-subscription-request.html', context)


@csrf_exempt
@require_POST
def patient_subscription_request_submit(request):
    """
    Handle patient subscription request form submission
    """
    if not request.user.is_authenticated or request.user.user_type != 'patient':
        return JsonResponse({'error': 'Unauthorized', 'status': 'error'}, status=401)
    
    try:
        # Check for existing active or pending subscription
        from django.utils import timezone
        today = timezone.now().date()
        
        existing_subscription = request.user.subscriptions.filter(
            subscription_plan__user_type='patient'
        ).order_by('-created_at').first()
        
        if existing_subscription:
            if existing_subscription.is_active and existing_subscription.start_date <= today <= existing_subscription.end_date:
                return JsonResponse({
                    'status': 'error',
                    'message': 'You already have an active subscription'
                }, status=400)
            
            if not existing_subscription.is_active and existing_subscription.status == 'pending':
                return JsonResponse({
                    'status': 'error',
                    'message': 'You already have a pending subscription request'
                }, status=400)
        
        # Get form data
        plan_id = request.POST.get('plan_id')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        duration_months = request.POST.get('duration_months')
        final_amount = request.POST.get('final_amount')
        payment_screenshot = request.FILES.get('payment_screenshot')
        payment_message = request.POST.get('payment_message', '')
        
        # Validate required fields
        if not all([plan_id, start_date, end_date, duration_months, final_amount, payment_screenshot]):
            return JsonResponse({
                'status': 'error',
                'message': 'All fields are required'
            }, status=400)
        
        # Get subscription plan
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id, user_type='patient', is_active=True)
        except SubscriptionPlan.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid subscription plan'
            }, status=400)
        
        # Validate dates
        from datetime import datetime
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid date format'
            }, status=400)
        
        if start_date_obj < today:
            return JsonResponse({
                'status': 'error',
                'message': 'Start date cannot be in the past'
            }, status=400)
        
        # Create subscription request
        subscription = UserSubscription.objects.create(
            user=request.user,
            subscription_plan=plan,
            start_date=start_date_obj,
            end_date=end_date_obj,
            duration_in_months=int(duration_months),
            final_amount_paid=int(final_amount),
            payment_screenshot=payment_screenshot,
            payment_message=payment_message,
            is_active=False,  # Admin will activate after verification
            status='pending'
        )
        
        logger.info(f"Patient subscription request created: ID={subscription.id}, User={request.user.email}")
        
        return JsonResponse({
            'status': 'success',
            'message': 'Subscription request submitted successfully',
            'subscription_id': subscription.id
        })
        
    except Exception as e:
        logger.error(f"Error submitting patient subscription request: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'An error occurred while processing your request'
        }, status=500)
