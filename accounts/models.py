
import uuid
from collections import defaultdict
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
import random
import string
from datetime import timedelta
# ---------- User + Manager ----------

class CustomUserManager(BaseUserManager):
    def create_user(self, email, phone_number=None, password=None, user_type='patient', **extra_fields):
        if not email:
            raise ValueError('The Email must be set')
        if not password:
            raise ValueError('The Password must be set')

        email = self.normalize_email(email)
        user = self.model(
            email=email,
            phone_number=phone_number,
            user_type=user_type,
            **extra_fields
        )
        user.set_password(password)

        if user_type == 'admin':
            user.username = 'admin'
        elif user_type == 'staff':
            user.username = 'staff'
        else:
            user.username = None 

        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        if not password:
            raise ValueError("Superuser must have a password")

        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        user = self.create_user(
            email=email,
            password=password,
            user_type='admin',   
            **extra_fields
        )
        user.is_active = True
        user.username = 'admin'
        user.save(using=self._db)
        return user

class CustomUser(AbstractBaseUser, PermissionsMixin):
    USER_TYPES = (
        ('patient', 'Patient'),
        ('doctor', 'Doctor'),
        ('hospital', 'Hospital'),
        ('admin', 'Admin'),
        ('staff', 'Staff'),
    )

    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
    user_type = models.CharField(max_length=10, choices=USER_TYPES)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    username = models.CharField(max_length=150, null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone_number']

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    @property
    def is_patient(self): return self.user_type == 'patient'
    @property
    def is_doctor(self): return self.user_type == 'doctor'
    @property
    def is_hospital(self): return self.user_type == 'hospital'

    def update_username_from_profile(self):
        """Auto-assign username based on user type and related profile"""
        if self.user_type == 'patient' and hasattr(self, 'patient_profile'):
            self.username = self.patient_profile.full_name
        elif self.user_type == 'doctor' and hasattr(self, 'doctor_profile'):
            self.username = self.doctor_profile.doctor_name
        elif self.user_type == 'hospital' and hasattr(self, 'hospital_profile'):
            self.username = self.hospital_profile.name
        elif self.user_type == 'admin':
            self.username = 'admin'
        elif self.user_type == 'staff':
            self.username = 'staff'
        self.save(update_fields=['username'])




# ---------- Profiles ----------
class PatientProfile(models.Model):
    GENDER_CHOICES = (('M','Male'),('F','Female'),('O','Other'))
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='patient_profile')
    full_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True)
    address = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=15, blank=True)
    blood_group = models.CharField(max_length=5, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def age(self):
        if not self.date_of_birth:
            return None
        today = timezone.now().date()
        dob = self.date_of_birth
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


class Specialization(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    def __str__(self): return self.name


class DoctorProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='doctor_profile')
    doctor_name = models.CharField(max_length=100)
    education = models.TextField(blank=True)
    experience = models.PositiveSmallIntegerField(default=0, validators=[MinValueValidator(0)])
    specializations = models.ManyToManyField(Specialization, related_name='doctors', blank=True)
    license_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    consultation_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    bio = models.TextField(blank=True)

    # Prefer normalized locations for filtering/search
    country = models.CharField()
    state = models.CharField()
    city = models.CharField()
    address = models.TextField()
    pincode = models.CharField()

    languages_spoken = models.CharField(max_length=200, blank=True)
    awards_certifications = models.TextField(blank=True)
    is_available = models.BooleanField(default=True)
    availability_last_updated = models.DateTimeField(auto_now=True)

    # performance metrics (cached for fast sorting)
    rating_avg = models.FloatField(default=0.0)
    num_reviews = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['is_available','experience']),
            models.Index(fields=['rating_avg', 'num_reviews']),
        ]

    def __str__(self):
        return self.doctor_name


class DoctorWorkingHours(models.Model):
    """
    Stores doctor's weekly working hours (Monday-Sunday).
    Each doctor must have all 7 days defined.
    """
    DAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]

    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='working_hours')
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField(null=True, blank=True, help_text="Leave blank if day is off")
    end_time = models.TimeField(null=True, blank=True, help_text="Leave blank if day is off")
    is_off = models.BooleanField(default=False, help_text="Check if doctor is off on this day")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('doctor', 'day_of_week')
        ordering = ['day_of_week']

    def __str__(self):
        return f"{self.doctor.doctor_name} - {self.get_day_of_week_display()}"

    def get_day_of_week_display(self):
        return dict(self.DAY_CHOICES).get(self.day_of_week, 'Unknown')


class MedicalEquipment(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    def __str__(self): return self.name


class HospitalClinicProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='hospital_profile')
    name = models.CharField(max_length=200)
    established_year = models.PositiveSmallIntegerField(null=True, blank=True)
    registration_number = models.CharField(max_length=100, null=True, blank=True)
    gst_number = models.CharField(max_length=50, null=True, blank=True)
    about = models.TextField(blank=True)
    country = models.CharField()
    state = models.CharField()
    city = models.CharField()
    address = models.TextField()
    pincode = models.CharField()
    website = models.URLField(blank=True)

    medical_equipments = models.TextField(blank=True)
    facilities = models.TextField(blank=True)
    emergency_services = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True, help_text="Hospital is open for appointments")
    availability_last_updated = models.DateTimeField(auto_now=True, help_text="Last time availability was toggled")

    rating_avg = models.FloatField(default=0.0)
    num_reviews = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total_doctors(self):
        return self.doctors.count()

    def __str__(self):
        return self.name


class HospitalDoctors(models.Model):
    hospital = models.ForeignKey(HospitalClinicProfile, on_delete=models.CASCADE, related_name='doctors')
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE) 
    joining_date = models.DateField(default=timezone.now)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('hospital', 'doctor')


class HospitalWorkingHours(models.Model):
    """
    Stores hospital's weekly working hours (Monday-Sunday).
    Each hospital must have all 7 days defined.
    """
    DAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]

    hospital = models.ForeignKey(HospitalClinicProfile, on_delete=models.CASCADE, related_name='working_hours')
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField(null=True, blank=True, help_text="Leave blank if day is off")
    end_time = models.TimeField(null=True, blank=True, help_text="Leave blank if day is off")
    is_off = models.BooleanField(default=False, help_text="Check if hospital is closed on this day")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('hospital', 'day_of_week')

    def __str__(self):
        return f"{self.hospital.name} - {self.get_day_of_week_display()}"

    def get_day_of_week_display(self):
        return dict(self.DAY_CHOICES).get(self.day_of_week)


class OTP(models.Model):
    OTP_TYPE_CHOICES = (
        ("email", "Email"),
        ("phone", "Phone"),
    )

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="otp")
    code = models.CharField(max_length=6)
    otp_type = models.CharField(max_length=10, choices=OTP_TYPE_CHOICES, default="email")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"OTP for {self.user.email} ({self.otp_type})"

    def is_valid(self):
        """Check if OTP is still valid and not used"""
        return (not self.is_used) and timezone.now() < self.expires_at

    @staticmethod
    def generate_otp(length=6):
        """Generate random numeric OTP"""
        return ''.join(random.choices(string.digits, k=length))

    @classmethod
    def create_or_update_otp(cls, user, otp_type="email", validity_minutes=5):
        """
        Create new OTP if not exist OR update existing one (overwrite on resend)
        """
        code = cls.generate_otp()
        expires_at = timezone.now() + timedelta(minutes=validity_minutes)

        otp, created = cls.objects.update_or_create(
            user=user,
            defaults={
                "code": code,
                "otp_type": otp_type,
                "expires_at": expires_at,
                "is_used": False,
                "created_at": timezone.now(),
            },
        )
        return otp
    

class QuickContact(models.Model):
    phone_number_one = models.CharField(max_length=15)
    phone_number_two = models.CharField(max_length=15, blank=True, null=True)
    email_one = models.EmailField()
    email_two = models.EmailField(blank=True, null=True)
    address = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Quick Contact Information"

class ContactMessage(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('read', 'Read'),
        ('replied', 'Replied'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15, blank=True, null=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.subject} - {self.email}"



class Feedback(models.Model):
    ROLE_CHOICES = (
        ('patient', 'Patient/User'),
        ('doctor', 'Doctor'),
        ('hospital', 'Hospital/Clinic'),
        ('other', 'Other'),
    )
    
    SYMPTOMS_UNDERSTANDING_CHOICES = (
        ('absolutely', 'Absolutely'),
        ('little_confusion', 'Little Confusion'),
        ('no', 'No'),
    )
    
    ILLNESS_SUGGESTION_CHOICES = (
        ('right', 'Right'),
        ('almost_right', 'Almost Right'),
        ('incorrect', 'Incorrect'),
    )
    
    DOCTOR_SUGGESTION_CHOICES = (
        ('yes', 'Yes'),
        ('no', 'No'),
        ('not_required', 'Not Required'),
    )
    
    APPOINTMENT_CHOICES = (
        ('yes', 'Yes'),
        ('no', 'No'),
        ('not_required', 'Not Required'),
    )
    
    RATING_CHOICES = (
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Good'),
        (4, '4 - Very Good'),
        (5, '5 - Excellent'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=15, blank=True, null=True)
    
    # Role Information
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    age = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(120)],
        null=True,
        blank=True
    )
    address = models.TextField(blank=True)
    
    # Medical Feedback
    selected_body_parts = models.ManyToManyField("symptoms.BodyPart", blank=True)
    symptoms_understanding = models.CharField(
        max_length=20, 
        choices=SYMPTOMS_UNDERSTANDING_CHOICES,
        verbose_name="How well did you understand the symptoms analysis?"
    )
    illness_suggestion = models.CharField(
        max_length=15, 
        choices=ILLNESS_SUGGESTION_CHOICES,
        verbose_name="Was the illness suggestion accurate?"
    )
    helpful_doctor_suggestion = models.CharField(
        max_length=15, 
        choices=DOCTOR_SUGGESTION_CHOICES,
        verbose_name="Were the doctor suggestions helpful?"
    )
    want_appointment_feature = models.CharField(
        max_length=15, 
        choices=APPOINTMENT_CHOICES,
        blank=True,
        null=True,
        verbose_name="Do you want appointment booking feature?"
    )
    
    # General Feedback
    improvement_suggestion = models.TextField(
        blank=True,
        verbose_name="Suggestions for improvement"
    )
    rate_us = models.IntegerField(choices=RATING_CHOICES, verbose_name="Overall Rating")
    
    # Metadata
    is_anonymous = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Feedback"
        verbose_name_plural = "Feedback"
        ordering = ['-created_at']

    def __str__(self):
        return f"Feedback from {self.email} - Rating: {self.rate_us}/5"

    def get_user_role_display(self):
        """Get display name for role with proper formatting"""
        return dict(self.ROLE_CHOICES).get(self.role, self.role)


# -------------------- Subscriptions --------------------
class SubscriptionPlan(models.Model):
    USER_TYPE_CHOICES = (
        ('patient', 'Patient'),
        ('doctor', 'Doctor'),
        ('hospital', 'Hospital'),
    )

    name = models.CharField(max_length=200)
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)
    monthly_price = models.PositiveIntegerField(default=0)
    half_yearly_discount = models.PositiveIntegerField(default=0)
    yearly_discount = models.PositiveIntegerField(default=0)

    receiver_qr = models.FileField(upload_to='subscriptions/qr/', blank=True, null=True)
    receiver_banking_name = models.CharField(max_length=200, blank=True)

    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_user_type_display()})"


class UserSubscription(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending Verification'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('rejected', 'Rejected'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscriptions')
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name='user_subscriptions')
    start_date = models.DateField()
    end_date = models.DateField()
    duration_in_months = models.PositiveIntegerField()
    final_amount_paid = models.PositiveIntegerField()
    
    # Admin-controlled activation
    is_active = models.BooleanField(default=False, help_text="Admin activates after payment verification")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Payment proof
    payment_screenshot = models.ImageField(upload_to='subscriptions/payments/', null=True, blank=True)
    payment_message = models.TextField(blank=True, help_text="Message from user during payment submission")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True, help_text="When admin verified the payment")
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.subscription_plan.name} ({self.status})"
    
    def is_date_active(self):
        """Check if current date falls within subscription period"""
        from django.utils import timezone
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date
    
    def get_computed_status(self):
        """Compute status based on is_active flag and dates"""
        from django.utils import timezone
        today = timezone.now().date()
        
        if not self.is_active:
            return 'pending'
        elif today > self.end_date:
            return 'expired'
        elif self.start_date <= today <= self.end_date:
            return 'active'
        else:
            return 'pending'

# -------------------- Appointment Booking System --------------------
class Appointment(models.Model):
    """
    Appointment booking system for patients to book appointments.
    Supports two types of bookings:
    1. Doctor appointments (direct doctor booking)
    2. Hospital appointments (hospital booking without specific doctor)
    Note: Either doctor OR hospital must be set, but not both.
    """
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('CANCELED', 'Canceled'),
    )
    
    # Relationships
    patient = models.ForeignKey(
        PatientProfile, 
        on_delete=models.CASCADE, 
        related_name='appointments'
    )
    doctor = models.ForeignKey(
        DoctorProfile, 
        on_delete=models.CASCADE, 
        related_name='appointments',
        null=True,
        blank=True,
        help_text="Doctor for appointment (for doctor bookings)"
    )
    hospital = models.ForeignKey(
        HospitalClinicProfile,
        on_delete=models.CASCADE,
        related_name='appointments',
        null=True,
        blank=True,
        help_text="Hospital for appointment (for hospital bookings)"
    )
    
    # Appointment details
    appointment_date = models.DateField(
        help_text="Date of the appointment"
    )
    patient_message = models.TextField(
        blank=True,
        help_text="Patient's description of the issue or reason for appointment"
    )
    
    # Status management
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='PENDING'
    )
    
    # Doctor response (for ACCEPTED status)
    doctor_provided_time = models.TimeField(
        null=True, 
        blank=True,
        help_text="Approximate visit time provided by doctor upon acceptance"
    )
    
    # Rejection reason (for REJECTED status)
    rejection_reason = models.TextField(
        blank=True,
        help_text="Reason provided by doctor for rejection"
    )
    
    # Cancellation (for CANCELED status)
    cancellation_reason = models.TextField(
        blank=True,
        help_text="Reason provided by patient for cancellation"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['doctor', 'status']),
            models.Index(fields=['hospital', 'status']),
            models.Index(fields=['patient', 'status']),
            models.Index(fields=['appointment_date']),
        ]
    
    def __str__(self):
        if self.doctor:
            return f"Appointment: {self.patient.full_name} with Dr. {self.doctor.doctor_name} on {self.appointment_date}"
        elif self.hospital:
            return f"Appointment: {self.patient.full_name} at {self.hospital.name} on {self.appointment_date}"
        return f"Appointment: {self.patient.full_name} on {self.appointment_date}"
    
    def clean(self):
        """Validate that either doctor or hospital is set, but not both"""
        from django.core.exceptions import ValidationError
        if not self.doctor and not self.hospital:
            raise ValidationError("Either doctor or hospital must be specified.")
        if self.doctor and self.hospital:
            raise ValidationError("Cannot specify both doctor and hospital for the same appointment.")
    
    def is_pending(self):
        """Check if appointment is in pending status"""
        return self.status == 'PENDING'
    
    def is_accepted(self):
        """Check if appointment is accepted"""
        return self.status == 'ACCEPTED'
    
    def is_rejected(self):
        """Check if appointment is rejected"""
        return self.status == 'REJECTED'
    
    def is_canceled(self):
        """Check if appointment is canceled"""
        return self.status == 'CANCELED'
    
    def can_be_canceled(self):
        """Patient can only cancel pending appointments"""
        return self.status == 'PENDING'
    
    def can_be_accepted_or_rejected(self):
        """Doctor can only accept/reject pending appointments"""
        return self.status == 'PENDING'


# -------------------- Team Member --------------------
class TeamMember(models.Model):
    ROLE_CHOICES = (
        ('founder', 'Founder'),
        ('co_founder', 'Co-Founder'),
        ('developer', 'Developer'),
        ('designer', 'Designer'),
        ('doctor_advisor', 'Doctor / Medical Advisor'),
        ('data_scientist', 'Data Scientist'),
        ('marketing', 'Marketing'),
        ('support', 'Support'),
        ('other', 'Other'),
    )

    name = models.CharField(max_length=100)
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default='other')
    custom_role_label = models.CharField(
        max_length=100,
        blank=True,
        help_text="Override display role label (optional)"
    )
    short_bio = models.TextField(
        max_length=300,
        blank=True,
        help_text="Short bio shown on the homepage card"
    )
    photo = models.ImageField(
        upload_to='team/',
        null=True,
        blank=True,
        help_text="Team member photo (recommended 400x400px)"
    )
    linkedin_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)

    order = models.PositiveSmallIntegerField(
        default=0,
        help_text="Display order on homepage (lower = first)"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Team Member'
        verbose_name_plural = 'Team Members'

    def __str__(self):
        return f"{self.name} — {self.get_role_display_label()}"

    def get_role_display_label(self):
        if self.custom_role_label:
            return self.custom_role_label
        return dict(self.ROLE_CHOICES).get(self.role, self.role)