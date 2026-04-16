# accounts/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import PatientProfile, DoctorProfile, HospitalClinicProfile


@receiver(post_save, sender=PatientProfile)
def set_patient_username(sender, instance, created, **kwargs):
    if created:
        instance.user.update_username_from_profile()


@receiver(post_save, sender=DoctorProfile)
def set_doctor_username(sender, instance, created, **kwargs):
    if created:
        instance.user.update_username_from_profile()


@receiver(post_save, sender=HospitalClinicProfile)
def set_hospital_username(sender, instance, created, **kwargs):
    if created:
        instance.user.update_username_from_profile()
