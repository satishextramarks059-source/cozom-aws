from django.urls import path

from . import views

from .api_doctor_export_appointments import DoctorBookingsExportAPIView

urlpatterns = [
    path('patient-signup/', views.patient_signup, name='patient-signup'),
    path('hospital-signup/', views.hospital_signup, name='hospital-signup'),
    path('doctor-signup/', views.doctor_signup, name='doctor-signup'),

    path("api/register/patient/", views.PatientRegisterAPIView.as_view(), name="patient-register"),
    path("api/register/hospital/", views.HospitalRegisterAPIView.as_view(), name="hospital-register"),
    path("api/register/doctor/", views.DoctorRegisterAPIView.as_view(), name="doctor-register"),

    path("api/verify-otp/", views.VerifyOtpAPIView.as_view(), name="verify-otp"),
    path("api/resend-otp/", views.ResendOtpAPIView.as_view(), name="resend-otp"),
    path("api/cancel-registration/", views.CancelRegistrationAPIView.as_view(), name="cancel-registration"),
    path("api/check-email/", views.EmailUniqueCheckAPIView.as_view(), name="check-email"),
    path("api/check-contact-number/", views.ContactNumberUniqueCheckAPIView.as_view(), name="check-contact-number"),


    path("api/forgot-password/check/", views.ForgotPasswordCheckAPIView.as_view(), name="forgot-password-check"),
    path("api/forgot-password/verify-otp/", views.ForgotPasswordVerifyOtpAPIView.as_view(), name="forgot-password-verify-otp"),
    path("api/forgot-password/reset/", views.ForgotPasswordResetAPIView.as_view(), name="forgot-password-reset"),
    path("api/forgot-password/resend-otp/", views.ForgotPasswordResendOtpAPIView.as_view(), name="forgot-password-resend-otp"),
    path("api/forgot-password/cancel/", views.ForgotPasswordCancelAPIView.as_view(), name="forgot-password-cancel"),

    path("api/login/", views.login_view, name="login"),
    path("api/reset-password/", views.reset_password_view, name="reset-password"),
    path("api/logout/", views.logout_view, name="logout"),

    path('contact-us/', views.contact_us, name='contact_us'),
    path('submit-contact/', views.submit_contact, name='submit_contact'),

    path('feedback/', views.feedback, name='feedback'),
    path('submit-feedback/', views.submit_feedback, name='submit_feedback'),

    path('admin-dashboard/', views.admin_dashboard, name='admin-dashboard'),

    path('contact-messages-list/', views.contact_messages_list, name='contact-messages-list'),
    path('update-message-status/<int:message_id>/', views.update_message_status, name='update_message_status'),
    path('reply-to-message/<int:message_id>/', views.reply_to_message, name='reply_to_message'),

    path('feedback-list/', views.feedback_list, name='feedback-list'),
    path('feedback-detail/<int:pk>/', views.feedback_detail, name='feedback-detail'),

    path('registered-doctors-list/', views.registered_doctor_list_view, name='registered-doctors-list'),
    path('soft-delete-or-recover-account/<int:pk>/', views.account_delete_or_recover_view, name='soft-delete-or-recover-account'),
    path('registered-patients-list/', views.registered_patient_list_view, name='registered-patients-list'),
    path('registered-hospitals-list/', views.registered_hospital_list_view, name='registered-hospitals-list'),

    # Admin subscription management
    path('admin/subscriptions/', views.admin_subscriptions_list, name='admin-subscriptions-list'),
    path('admin/subscriptions/create/', views.admin_subscription_create, name='admin-subscriptions-create'),
    path('admin/subscriptions/<int:pk>/edit/', views.admin_subscription_edit, name='admin-subscriptions-edit'),
    path('admin/subscriptions/<int:pk>/delete/', views.admin_subscription_delete, name='admin-subscriptions-delete'),

    path('patient-dashboard/', views.patient_dashboard, name='patient-dashboard'),
    # Patient Subscription Management
    path('patient/subscription/request/', views.patient_subscription_request_page, name='patient-subscription-request-page'),
    path('api/patient/subscription/submit/', views.patient_subscription_request_submit, name='patient-subscription-request-submit'),

    # Doctor Dashboard
    path('doctor-dashboard/', views.doctor_dashboard, name='doctor-dashboard'),
    path('api/doctor/toggle-availability/', views.toggle_doctor_availability, name='toggle-doctor-availability'),
    path('api/doctor/working-hours/', views.get_doctor_working_hours, name='get-working-hours'),
    path('api/doctor/working-hours/save/', views.save_doctor_working_hours, name='save-working-hours'),
    # Doctor Bookings Export
    path('api/doctor/export-bookings/', DoctorBookingsExportAPIView.as_view(), name='doctor-export-bookings'),
    
    # Subscription Management
    path('subscription/request/', views.subscription_request_page, name='subscription-request-page'),
    path('api/subscription/submit/', views.subscription_request_submit, name='subscription-request-submit'),

    # Hospital Dashboard
    path('hospital-dashboard/', views.hospital_dashboard, name='hospital-dashboard'),
    path('api/hospital/toggle-availability/', views.toggle_hospital_availability, name='toggle-hospital-availability'),
    path('api/hospital/working-hours/', views.get_hospital_working_hours, name='get-hospital-working-hours'),
    path('api/hospital/working-hours/save/', views.save_hospital_working_hours, name='save-hospital-working-hours'),
    # Hospital Bookings Export
    path('api/hospital/export-bookings/', views.HospitalBookingsExportAPIView.as_view(), name='hospital-export-bookings'),
    # Hospital Subscription Management
    path('hospital/subscription/request/', views.hospital_subscription_request_page, name='hospital-subscription-request-page'),
    path('api/hospital/subscription/submit/', views.hospital_subscription_request_submit, name='hospital-subscription-request-submit'),

    # Appointment Booking System
    path('api/appointments/create/', views.AppointmentCreateAPIView.as_view(), name='appointment-create'),
    path('api/appointments/list/', views.AppointmentListAPIView.as_view(), name='appointment-list'),
    path('api/appointments/<int:appointment_id>/accept/', views.AppointmentAcceptAPIView.as_view(), name='appointment-accept'),
    path('api/appointments/<int:appointment_id>/reject/', views.AppointmentRejectAPIView.as_view(), name='appointment-reject'),
    path('api/appointments/<int:appointment_id>/cancel/', views.AppointmentCancelAPIView.as_view(), name='appointment-cancel'),
    path('api/appointments/pending-count/', views.get_pending_appointments_count, name='appointment-pending-count'),
    path('appointments/<int:appointment_id>/download-pdf/', views.download_appointment_pdf, name='download-appointment-pdf'),

]
