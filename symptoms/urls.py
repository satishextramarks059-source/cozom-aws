from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('services/', views.services, name='services'),
    path('symptom-check/', views.SymptomCheckView.as_view(), name='symptom-check-page'),
    path('api/symptom-check/', views.SymptomCheckAPIView.as_view(), name='symptom-check-api'),
    path('api/doctors-by-specialist/', views.DoctorsBySpecialistView.as_view(), name='doctors-by-specialist-api'),
    path('recommended-doctors/', views.RecommendedDoctorListingView.as_view(), name='recommended-doctor-listing'),
    path('registered-doctors/', views.RegisteredDoctorsListingView.as_view(), name='registered-doctors-listing'),
    path('api/registered-doctors/', views.RegisteredDoctorsAPIView.as_view(), name='registered-doctors-api'),
    path('find-hospitals/', views.FindHospitalsListingView.as_view(), name='find-hospitals-listing'),
    path('api/hospitals/', views.HospitalsAPIView.as_view(), name='hospitals-api'),
    
    # Illness Details API for Symptom Checker Modal
    path('api/illness/<int:illness_id>/details/', views.IllnessDetailsAPIView.as_view(), name='illness-details'),
]