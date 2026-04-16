from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.http import HttpResponse
import csv
from accounts.models import Appointment

class DoctorBookingsExportAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        status_param = request.GET.get('status')
        if status_param not in ['accepted', 'rejected']:
            return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)

        if not hasattr(request.user, 'doctor_profile'):
            return Response({'error': 'Not a doctor'}, status=status.HTTP_403_FORBIDDEN)
        doctor = request.user.doctor_profile

        # Map status_param to DB status
        status_map = {'accepted': 'ACCEPTED', 'rejected': 'REJECTED'}
        db_status = status_map[status_param]
        appointments = Appointment.objects.filter(doctor=doctor, status=db_status).select_related('patient__user')

        # CSV file naming
        today_str = timezone.now().date().strftime('%Y-%m-%d')
        filename = f"{status_param}_bookings_{today_str}.csv"

        # CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        writer = csv.writer(response)

        # Write header
        writer.writerow([
            'Patient Full Name',
            'Appointment Date',
            'Patient Phone',
            'Patient Email',
            'Patient Address',
            'Patient Message',
            'Status',
            'Doctor Response',
        ])

        for appt in appointments:
            patient = appt.patient
            user = patient.user
            doctor_response = ''
            if db_status == 'ACCEPTED':
                doctor_response = appt.doctor_provided_time.strftime('%I:%M %p') if appt.doctor_provided_time else ''
            elif db_status == 'REJECTED':
                doctor_response = appt.rejection_reason or ''
            writer.writerow([
                patient.full_name,
                appt.appointment_date.strftime('%Y-%m-%d'),
                user.phone_number,
                user.email,
                patient.address,
                appt.patient_message,
                db_status.capitalize(),
                doctor_response,
            ])
        return response
