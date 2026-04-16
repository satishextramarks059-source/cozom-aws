from .models import *

def user_profile_name(request):
    if request.user.is_authenticated:
        try:
            if request.user.is_patient:
                return {'profile_name': PatientProfile.objects.get(user=request.user).full_name}
            elif request.user.is_doctor:
                return {'profile_name': DoctorProfile.objects.get(user=request.user).doctor_name}
            elif request.user.is_hospital:
                return {'profile_name': HospitalClinicProfile.objects.get(user=request.user).name}
            else:
                return {'profile_name': request.user.email}
        except Exception:
            return {'profile_name': request.user.email}
    return {}