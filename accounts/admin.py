from django.contrib import admin
from .models import (
    CustomUser,
    PatientProfile, DoctorProfile, Specialization,
    HospitalClinicProfile, HospitalDoctors, MedicalEquipment, OTP, ContactMessage, QuickContact, Feedback,DoctorWorkingHours,
    Appointment, TeamMember
)
from .models import SubscriptionPlan, UserSubscription


# ------------------- CustomUser -------------------
@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    # Fields to display in list view
    list_display = ('email', 'phone_number', 'user_type', 'is_active', 'is_verified', 'is_staff', 'date_joined')

    # Filters for sidebar
    list_filter = ('is_active', 'is_verified', 'is_staff', 'user_type')

    # Search fields
    search_fields = ('email', 'phone_number', 'email', 'user_type')

    # Optional: ordering by newest users first
    ordering = ('-date_joined',)

    # Optional: fields editable in list view
    list_editable = ('is_active', 'is_verified', 'is_staff')


# ------------------- Profiles -------------------
@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'gender', 'date_of_birth')
    search_fields = ('full_name', 'user__email', 'user__phone_number')
    list_filter = ('gender',)


@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ('doctor_name', 'user', 'experience', 'is_available', 'rating_avg', 'num_reviews')
    search_fields = ('doctor_name', 'user__email', 'user__phone_number', 'specializations__name')
    list_filter = ('is_available', 'specializations')


@admin.register(Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(HospitalClinicProfile)
class HospitalClinicProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'established_year', 'rating_avg', 'num_reviews', 'emergency_services')
    search_fields = ('name', 'user__email', 'user__phone_number', 'registration_number', 'gst_number')
    list_filter = ('emergency_services', 'country', 'state')


@admin.register(HospitalDoctors)
class HospitalDoctorsAdmin(admin.ModelAdmin):
    list_display = ('hospital', 'doctor', 'joining_date', 'is_active')
    list_filter = ('is_active', 'hospital')
    search_fields = ('doctor__doctor_name', 'hospital__name')


@admin.register(MedicalEquipment)
class MedicalEquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'otp_type', 'code', 'is_used', 'created_at', 'expires_at')
    list_filter = ('otp_type', 'is_used')
    search_fields = ('user__email', 'user__phone_number', 'code')


# ------------------- Location Models -------------------
# Country, State, District models are not used in this version
# Location information is stored as CharField in DoctorProfile and HospitalClinicProfile


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['subject', 'email', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['subject', 'email', 'name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(QuickContact)
class QuickContactAdmin(admin.ModelAdmin):
    list_display = ['phone_number_one', 'email_one', 'is_active']
    
    def has_add_permission(self, request):
        # Allow only one active QuickContact instance
        if QuickContact.objects.filter(is_active=True).exists():
            return False
        return super().has_add_permission(request)



@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'email',
        'phone',
        'role',
        'rate_us',
        'symptoms_understanding',
        'illness_suggestion',
        'helpful_doctor_suggestion',
        'want_appointment_feature',
        'created_at',
    )

    list_filter = (
        'role',
        'rate_us',
        'symptoms_understanding',
        'illness_suggestion',
        'helpful_doctor_suggestion',
        'want_appointment_feature',
        'is_anonymous',
        'created_at',
    )

    search_fields = (
        'email',
        'phone',
        'address',
        'improvement_suggestion',
        'user__username',
        'user__email',
    )

    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ('user', 'selected_body_parts')

    fieldsets = (
        ('User Information', {
            'fields': ('user', 'email', 'phone', 'role', 'age', 'address', 'is_anonymous'),
        }),
        ('Medical Feedback', {
            'fields': (
                'selected_body_parts',
                'symptoms_understanding',
                'illness_suggestion',
                'helpful_doctor_suggestion',
                'want_appointment_feature',
            ),
        }),
        ('General Feedback', {
            'fields': ('improvement_suggestion', 'rate_us'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )

    ordering = ('-created_at',)
    list_per_page = 25


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'user_type', 'monthly_price', 'is_active', 'created_at')
    list_filter = ('user_type', 'is_active')
    search_fields = ('name', 'receiver_banking_name')


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'subscription_plan', 'start_date', 'end_date', 'final_amount_paid')
    list_filter = ('subscription_plan',)
    search_fields = ('user__email', 'subscription_plan__name')

@admin.register(DoctorWorkingHours)
class DoctorWorkingHoursAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'day_of_week', 'start_time', 'end_time')
    list_filter = ('day_of_week',)
    search_fields = ('doctor__doctor_name',)


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'doctor', 'appointment_date', 'status', 'created_at')
    list_filter = ('status', 'appointment_date', 'created_at')
    search_fields = ('patient__full_name', 'doctor__doctor_name', 'patient__user__email', 'doctor__user__email')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    date_hierarchy = 'appointment_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('patient', 'doctor', 'appointment_date', 'status')
        }),
        ('Details', {
            'fields': ('patient_message', 'doctor_provided_time', 'rejection_reason', 'cancellation_reason')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_role_display_label', 'order', 'is_active', 'created_at')
    list_filter = ('role', 'is_active')
    search_fields = ('name', 'custom_role_label', 'short_bio')
    list_editable = ('order', 'is_active')
    ordering = ('order', 'name')
