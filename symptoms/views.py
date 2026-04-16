from django.shortcuts import render, redirect, HttpResponse
from django.views.decorators.http import require_http_methods
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.text import Truncator
from django.conf import settings
import logging
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
from django.http import JsonResponse
from django.views import View
from django.middleware.csrf import get_token

from .models import BodyPart, Symptom, SymptomCheckSession, SelectedSymptom, Illness, SymptomCheckResult
from accounts.models import DoctorProfile, HospitalClinicProfile
from accounts.models import Specialization
from accounts.models import HospitalDoctors

logger = logging.getLogger("symptoms")


def home(request):
    user_type = request.session.get("user_type")
    is_verified = request.session.get("is_verified")
    is_active = request.session.get("is_active")
    is_staff = request.session.get("is_staff")
    return render(request, 'home.html')


class SymptomCheckView(View):
    def get(self, request):
        get_token(request)
        return render(request, 'symptoms/symptom_checks.html')


# ==================== ILLNESS DETAILS API ====================

class IllnessDetailsAPIView(APIView):
    """Get detailed illness information with symptoms list"""
    
    def get(self, request, illness_id):
        try:
            illness = Illness.objects.get(id=illness_id)
            symptoms = illness.illness_symptoms.all()
            
            data = {
                'status': 'success',
                'illness': {
                    'id': illness.id,
                    'name': illness.name,
                    'description': illness.description,
                    'severity': illness.severity,
                    'treatment_advice': illness.treatment_advice,
                    'when_to_see_doctor': illness.when_to_see_doctor,
                    'specializations': [s.name for s in illness.specializations.all()],
                    'symptoms': [s.symptom.name for s in symptoms]
                }
            }
            return Response(data, status=status.HTTP_200_OK)
        except Illness.DoesNotExist:
            return Response({'status': 'error', 'error': 'Illness not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'status': 'error', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class SymptomCheckAPIView(View):
    def get(self, request):
        try:
            body_parts = BodyPart.objects.all()
            body_parts_data = []
            for part in body_parts:
                icon_url = None
                if part.icon:
                    icon_url = request.build_absolute_uri(part.icon.url)
                body_parts_data.append({
                    'id': part.id,
                    'name': part.name,
                    'icon': icon_url,
                    'description': part.description
                })
            return JsonResponse({
                'body_parts': body_parts_data,
                'status': 'success'
            })
        except Exception as e:
            return JsonResponse({
                'error': str(e),
                'status': 'error'
            }, status=500)

    def post(self, request):
        try:
            data = json.loads(request.body)
            step = data.get('step')

            if step == 'get_symptoms':
                body_part_ids = data.get('body_part_ids', [])
                symptoms = Symptom.objects.filter(
                    body_parts__id__in=body_part_ids
                ).distinct().values('id', 'name', 'description')
                return JsonResponse({
                    'symptoms': list(symptoms),
                    'status': 'success'
                })

            elif step == 'calculate_results':
                symptoms_with_severity = data.get('symptoms_with_severity', [])

                # Create session
                session = SymptomCheckSession.objects.create()

                # Store selected symptoms with severity
                for symptom_data in symptoms_with_severity:
                    SelectedSymptom.objects.create(
                        session=session,
                        symptom_id=symptom_data['symptom_id'],
                        user_severity=symptom_data['severity']
                    )

                # Convert selected symptom IDs to integers for proper comparison
                selected_symptom_ids = [int(s['symptom_id']) for s in symptoms_with_severity]

                # Calculate probabilities using doctor-thinking algorithm (returns final_score)
                results_data = session.calculate_illness_probabilities(symptoms_with_severity)

                # Store results
                results = []
                for result in results_data:
                    illness = result['illness']
                    final_score = result['final_score']          # 0–1 score
                    matched_count = result['matched_symptoms_count']
                    total_count = result['total_illness_symptoms']

                    # Get all symptoms of this illness with matched flag via IllnessSymptom
                    symptoms_with_match = []
                    illness_symptoms_qs = illness.illness_symptoms.select_related('symptom')
                    for illness_symptom in illness_symptoms_qs:
                        symptom = illness_symptom.symptom
                        matched = symptom.id in selected_symptom_ids
                        symptoms_with_match.append({
                            'id': symptom.id,
                            'name': symptom.name,
                            'description': symptom.description,
                            'matched': matched
                        })

                    # Store result in database (probability_score now holds final_score)
                    symptom_result = SymptomCheckResult.objects.create(
                        session=session,
                        illness=illness,
                        probability_score=final_score,
                        reasoning=f"Matched {matched_count} out of {total_count} symptoms"
                    )

                    # Get recommended specializations
                    specializations = illness.specializations.all().values('id', 'name')
                    specializations_list = list(specializations)
                    primary_specialist = specializations_list[0]['name'] if specializations_list else 'General Practitioner'
                    primary_specialist_id = specializations_list[0]['id'] if specializations_list else None

                    results.append({
                        'illness': {
                            'id': illness.id,
                            'name': illness.name,
                            'description': illness.description,
                            'severity': illness.severity,
                            'treatment_advice': illness.treatment_advice,
                            'when_to_see_doctor': illness.when_to_see_doctor,
                            'symptoms': symptoms_with_match,
                        },
                        'final_score': final_score,                                 # new field for frontend
                        'probability_score': final_score,                           # backward compatibility
                        'probability_percentage': round(final_score * 100),         # derived
                        'matched_symptoms': matched_count,
                        'total_symptoms': total_count,
                        'matched_symptom_names': [s['name'] for s in symptoms_with_match if s['matched']],
                        'all_symptom_names': [s['name'] for s in symptoms_with_match],
                        'recommended_specialists': specializations_list,
                        'primary_specialist': primary_specialist,
                        'primary_specialist_id': primary_specialist_id,
                        'reasoning': symptom_result.reasoning
                    })

                return JsonResponse({
                    'results': results,
                    'session_id': str(session.id),
                    'status': 'success'
                })

            elif step == 'ai_results':
                symptoms_with_severity = data.get('symptoms_with_severity', [])
                symptom_names = []
                for symptom_data in symptoms_with_severity:
                    symptom = Symptom.objects.get(id=symptom_data['symptom_id'])
                    symptom_names.append(f"{symptom.name} ({symptom_data['severity']} severity)")
                ai_results = self.get_ai_diagnosis(symptom_names)
                return JsonResponse({
                    'results': ai_results,
                    'source': 'ai',
                    'status': 'success'
                })

            else:
                return JsonResponse({
                    'error': 'Invalid step parameter',
                    'status': 'error'
                }, status=400)

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(error_details)
            return JsonResponse({
                'error': str(e),
                'status': 'error',
                'traceback': error_details
            }, status=500)

    def get_ai_diagnosis(self, symptoms_list):
        try:
            if any('cough' in symptom.lower() for symptom in symptoms_list) and any('fever' in symptom.lower() for symptom in symptoms_list):
                return [
                    {
                        'illness': {
                            'name': 'AI Analysis: Respiratory Infection',
                            'description': 'Based on your symptoms, this appears to be a respiratory tract infection possibly caused by viruses or bacteria.',
                            'severity': 'medium',
                            'treatment_advice': 'Rest, hydration, over-the-counter fever reducers, and cough medicine. Use a humidifier to ease breathing.',
                            'when_to_see_doctor': 'If symptoms worsen, difficulty breathing develops, or fever persists beyond 3 days.'
                        },
                        'final_score': 0.78,
                        'probability_percentage': 78,
                        'ai_notes': 'The combination of respiratory symptoms with fever suggests an infectious process. Monitor your temperature and breathing patterns.',
                        'confidence': 'high'
                    }
                ]
            elif any('headache' in symptom.lower() for symptom in symptoms_list) and any('nausea' in symptom.lower() for symptom in symptoms_list):
                return [
                    {
                        'illness': {
                            'name': 'AI Analysis: Migraine or Tension Headache',
                            'description': 'Your symptom pattern suggests migraine or severe tension headache, possibly triggered by stress, dehydration, or other factors.',
                            'severity': 'medium',
                            'treatment_advice': 'Rest in a quiet, dark room. Stay hydrated. Over-the-counter pain relievers may help. Identify and avoid triggers.',
                            'when_to_see_doctor': 'If headaches are severe, frequent, or accompanied by vision changes, weakness, or confusion.'
                        },
                        'final_score': 0.65,
                        'probability_percentage': 65,
                        'ai_notes': 'The association of headache with nausea is characteristic of migraines. Track frequency and potential triggers.',
                        'confidence': 'medium'
                    }
                ]
            else:
                return [
                    {
                        'illness': {
                            'name': 'AI Analysis: General Viral Syndrome',
                            'description': 'Your symptoms suggest a general viral infection. The body is mounting an immune response to fight off the infection.',
                            'severity': 'low',
                            'treatment_advice': 'Adequate rest, hydration, and proper nutrition. Over-the-counter symptom relief as needed.',
                            'when_to_see_doctor': 'If symptoms persist beyond 10-14 days, worsen significantly, or new concerning symptoms develop.'
                        },
                        'final_score': 0.45,
                        'probability_percentage': 45,
                        'ai_notes': 'Multiple generalized symptoms often indicate viral infections that typically resolve with supportive care.',
                        'confidence': 'medium'
                    }
                ]
        except Exception as e:
            print(f"AI diagnosis error: {e}")
            return [
                {
                    'illness': {
                        'name': 'AI Analysis Unavailable',
                        'description': 'Unable to generate AI analysis at this time. Please try the standard symptom checker.',
                        'severity': 'low',
                        'treatment_advice': 'Consult with a healthcare professional for proper diagnosis.',
                        'when_to_see_doctor': 'If symptoms concern you or persist.'
                    },
                    'final_score': 0.0,
                    'probability_percentage': 0,
                    'ai_notes': 'Technical difficulty in generating AI analysis. Please try again later.',
                    'confidence': 'low'
                }
            ]


@method_decorator(csrf_exempt, name='dispatch')
class DoctorsBySpecialistView(View):
    def get(self, request):
        try:
            specialist_id = request.GET.get('specialist_id')
            illness_name = request.GET.get('illness_name', '')
            page = int(request.GET.get('page', 1))
            per_page = 20

            if not specialist_id:
                return JsonResponse({
                    'error': 'specialist_id parameter is required',
                    'status': 'error'
                }, status=400)

            try:
                specialization = Specialization.objects.get(id=specialist_id)
            except Specialization.DoesNotExist:
                return JsonResponse({
                    'doctors': [],
                    'total_count': 0,
                    'page': page,
                    'total_pages': 0,
                    'status': 'success',
                    'message': 'No specialization found'
                })

            doctors = DoctorProfile.objects.filter(
                specializations=specialization, user__is_verified=True
            ).select_related('user').order_by('-rating_avg', '-num_reviews')

            total_count = doctors.count()
            total_pages = (total_count + per_page - 1) // per_page

            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            paginated_doctors = doctors[start_idx:end_idx]

            doctors_data = []
            for doctor in paginated_doctors:
                hospital_name = None
                try:
                    hospital_doc = HospitalDoctors.objects.filter(doctor=doctor, is_active=True).first()
                    if hospital_doc:
                        hospital_name = hospital_doc.hospital.name
                except:
                    pass

                working_hours = []
                day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                from accounts.models import DoctorWorkingHours
                for day_num in range(7):
                    try:
                        wh = DoctorWorkingHours.objects.get(doctor=doctor, day_of_week=day_num)
                        working_hours.append({
                            'day': day_num,
                            'day_name': day_names[day_num],
                            'is_off': wh.is_off,
                            'start_time': wh.start_time.strftime('%H:%M') if wh.start_time else None,
                            'end_time': wh.end_time.strftime('%H:%M') if wh.end_time else None
                        })
                    except DoctorWorkingHours.DoesNotExist:
                        working_hours.append({
                            'day': day_num,
                            'day_name': day_names[day_num],
                            'is_off': False,
                            'start_time': None,
                            'end_time': None
                        })

                doctors_data.append({
                    'id': doctor.id,
                    'name': doctor.doctor_name,
                    'education': doctor.education,
                    'experience': doctor.experience,
                    'rating': doctor.rating_avg,
                    'reviews': doctor.num_reviews,
                    'hospital': hospital_name,
                    'consultation_fee': str(doctor.consultation_fee),
                    'bio': doctor.bio,
                    'languages': doctor.languages_spoken,
                    'is_available': doctor.is_available,
                    'country': doctor.country,
                    'state': doctor.state,
                    'city': doctor.city,
                    'address': doctor.address,
                    'working_hours': working_hours
                })

            return JsonResponse({
                'doctors': doctors_data,
                'specialist': specialization.name,
                'illness_name': illness_name,
                'total_count': total_count,
                'page': page,
                'total_pages': total_pages,
                'per_page': per_page,
                'status': 'success'
            })

        except Exception as e:
            logger.error(f"Error fetching doctors by specialist: {str(e)}")
            return JsonResponse({
                'error': str(e),
                'status': 'error'
            }, status=500)


class RecommendedDoctorListingView(View):
    def get(self, request):
        specialist_id = request.GET.get('specialist_id')
        illness_name = request.GET.get('illness_name', '')
        page = int(request.GET.get('page', 1))

        specialist_name = 'Specialist'
        if specialist_id:
            try:
                specialist = Specialization.objects.get(id=specialist_id)
                specialist_name = specialist.name
            except Specialization.DoesNotExist:
                pass

        context = {
            'specialist_id': specialist_id,
            'specialist_name': specialist_name,
            'illness_name': illness_name,
            'page': page,
        }
        return render(request, 'symptoms/recommended_doctor_listing.html', context)


@method_decorator(csrf_exempt, name='dispatch')
class RegisteredDoctorsAPIView(View):
    def get(self, request):
        action = request.GET.get('action', 'doctors')
        if action == 'locations':
            return self.get_unique_locations(request)
        else:
            return self.get_doctors(request)

    def get_doctors(self, request):
        try:
            specialization_id = request.GET.get('specialization_id', '').strip()
            country = request.GET.get('country', '').strip()
            state = request.GET.get('state', '').strip()
            city = request.GET.get('city', '').strip()
            page = int(request.GET.get('page', 1))
            per_page = 20

            if specialization_id == 'None' or not specialization_id:
                return JsonResponse({
                    'error': 'specialization_id parameter is required',
                    'status': 'error'
                }, status=400)

            try:
                specialization = Specialization.objects.get(id=specialization_id)
            except (Specialization.DoesNotExist, ValueError):
                return JsonResponse({
                    'doctors': [],
                    'total_count': 0,
                    'page': page,
                    'total_pages': 0,
                    'status': 'success',
                    'message': 'No specialization found'
                })

            doctors_query = DoctorProfile.objects.filter(
                specializations=specialization,
                user__is_verified=True,
                user__is_active=True
            ).select_related('user').order_by('-rating_avg', '-num_reviews')

            if country:
                doctors_query = doctors_query.filter(country__icontains=country)
            if state:
                doctors_query = doctors_query.filter(state__icontains=state)
            if city:
                doctors_query = doctors_query.filter(city__icontains=city)

            total_count = doctors_query.count()
            total_pages = (total_count + per_page - 1) // per_page

            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            paginated_doctors = doctors_query[start_idx:end_idx]

            doctors_data = []
            for doctor in paginated_doctors:
                hospital_name = None
                try:
                    hospital_doc = HospitalDoctors.objects.filter(doctor=doctor, is_active=True).first()
                    if hospital_doc:
                        hospital_name = hospital_doc.hospital.name
                except:
                    pass

                working_hours = []
                day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                from accounts.models import DoctorWorkingHours
                for day_num in range(7):
                    try:
                        wh = DoctorWorkingHours.objects.get(doctor=doctor, day_of_week=day_num)
                        working_hours.append({
                            'day': day_num,
                            'day_name': day_names[day_num],
                            'is_off': wh.is_off,
                            'start_time': wh.start_time.strftime('%H:%M') if wh.start_time else None,
                            'end_time': wh.end_time.strftime('%H:%M') if wh.end_time else None
                        })
                    except DoctorWorkingHours.DoesNotExist:
                        working_hours.append({
                            'day': day_num,
                            'day_name': day_names[day_num],
                            'is_off': False,
                            'start_time': None,
                            'end_time': None
                        })

                doctors_data.append({
                    'id': doctor.id,
                    'name': doctor.doctor_name,
                    'education': doctor.education,
                    'experience': doctor.experience,
                    'rating': doctor.rating_avg,
                    'reviews': doctor.num_reviews,
                    'hospital': hospital_name,
                    'consultation_fee': str(doctor.consultation_fee),
                    'bio': doctor.bio,
                    'languages': doctor.languages_spoken,
                    'is_available': doctor.is_available,
                    'location': f"{doctor.city}, {doctor.state}, {doctor.country}" if doctor.city else f"{doctor.state}, {doctor.country}",
                    'country': doctor.country,
                    'state': doctor.state,
                    'city': doctor.city,
                    'address': doctor.address,
                    'working_hours': working_hours
                })

            return JsonResponse({
                'doctors': doctors_data,
                'specialist': specialization.name,
                'filters': {
                    'country': country,
                    'state': state,
                    'city': city,
                },
                'total_count': total_count,
                'page': page,
                'total_pages': total_pages,
                'per_page': per_page,
                'status': 'success'
            })

        except Exception as e:
            logger.error(f"Error fetching registered doctors: {str(e)}")
            return JsonResponse({
                'error': str(e),
                'status': 'error'
            }, status=500)

    def get_unique_locations(self, request):
        try:
            specialization_id = request.GET.get('specialization_id', '').strip()
            location_type = request.GET.get('type', '').strip()
            country = request.GET.get('country', '').strip()
            state = request.GET.get('state', '').strip()

            if specialization_id == 'None':
                specialization_id = ''

            if not specialization_id or not location_type:
                return JsonResponse({'error': 'Missing parameters', 'status': 'error'}, status=400)

            try:
                specialization = Specialization.objects.get(id=specialization_id)
            except (Specialization.DoesNotExist, ValueError):
                return JsonResponse({'locations': [], 'status': 'success'})

            query = DoctorProfile.objects.filter(
                specializations=specialization,
                user__is_verified=True,
                user__is_active=True
            ).distinct()

            locations = []

            if location_type == 'country':
                countries = query.values_list('country', flat=True).distinct().order_by('country')
                locations = [c for c in countries if c]

            elif location_type == 'state':
                if country:
                    query = query.filter(country__icontains=country)
                    states = query.values_list('state', flat=True).distinct().order_by('state')
                    locations = [s for s in states if s]

            elif location_type == 'city':
                if country:
                    query = query.filter(country__icontains=country)
                if state:
                    query = query.filter(state__icontains=state)
                    cities = query.values_list('city', flat=True).distinct().order_by('city')
                    locations = [c for c in cities if c]

            return JsonResponse({
                'locations': locations,
                'status': 'success'
            })

        except Exception as e:
            logger.error(f"Error fetching locations: {str(e)}")
            return JsonResponse({
                'error': str(e),
                'status': 'error'
            }, status=500)


class RegisteredDoctorsListingView(View):
    def get(self, request):
        specialization_id = request.GET.get('specialization_id')
        country = request.GET.get('country', '')
        state = request.GET.get('state', '')
        city = request.GET.get('city', '')
        page = int(request.GET.get('page', 1))

        specialist_name = 'All Specialists'
        if specialization_id:
            try:
                specialist = Specialization.objects.get(id=specialization_id)
                specialist_name = specialist.name
            except Specialization.DoesNotExist:
                pass

        specializations = Specialization.objects.all().order_by('name')

        context = {
            'specialization_id': specialization_id,
            'specialist_name': specialist_name,
            'specializations': specializations,
            'country': country,
            'state': state,
            'city': city,
            'page': page,
        }
        return render(request, 'symptoms/registered_doctors_listing.html', context)


# ==================== HOSPITAL FINDING VIEWS ====================

@method_decorator(csrf_exempt, name='dispatch')
class HospitalsAPIView(View):
    def get(self, request):
        action = request.GET.get('action', 'hospitals')
        
        if action == 'locations':
            return self.get_unique_locations(request)
        elif action == 'hospitals_list':
            return self.get_hospitals_list(request)
        else:
            return self.get_hospitals(request)
    
    def get_hospitals_list(self, request):
        try:
            hospitals = HospitalClinicProfile.objects.filter(
                user__is_verified=True,
                user__is_active=True,
                user__is_deleted=False
            ).order_by('name')
            
            hospitals_data = []
            for hospital in hospitals:
                hospitals_data.append({
                    'id': hospital.id,
                    'name': hospital.name,
                    'city': hospital.city or '',
                    'state': hospital.state or '',
                })
            
            return JsonResponse({
                'hospitals': hospitals_data,
                'status': 'success'
            })
        except Exception as e:
            logger.error(f"Error fetching hospitals list: {str(e)}")
            return JsonResponse({
                'error': str(e),
                'status': 'error'
            }, status=500)
    
    def get_hospitals(self, request):
        try:
            hospital_id = request.GET.get('hospital_id', '').strip()
            country = request.GET.get('country', '').strip()
            state = request.GET.get('state', '').strip()
            city = request.GET.get('city', '').strip()
            page = int(request.GET.get('page', 1))
            per_page = 20
            
            hospitals_query = HospitalClinicProfile.objects.filter(
                user__is_verified=True,
                user__is_active=True,
                user__is_deleted=False
            ).select_related('user').order_by('-rating_avg', '-num_reviews', 'name')
            
            if hospital_id and hospital_id != 'None':
                try:
                    hospitals_query = hospitals_query.filter(id=int(hospital_id))
                except ValueError:
                    pass
            
            if country:
                hospitals_query = hospitals_query.filter(country__iexact=country)
            if state:
                hospitals_query = hospitals_query.filter(state__iexact=state)
            if city:
                hospitals_query = hospitals_query.filter(city__iexact=city)
            
            total_count = hospitals_query.count()
            total_pages = (total_count + per_page - 1) // per_page
            
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            paginated_hospitals = hospitals_query[start_idx:end_idx]
            
            hospitals_data = []
            for hospital in paginated_hospitals:
                hospitals_data.append({
                    'id': hospital.id,
                    'name': hospital.name,
                    'established_year': hospital.established_year,
                    'rating': hospital.rating_avg,
                    'reviews': hospital.num_reviews,
                    'country': hospital.country or '',
                    'state': hospital.state or '',
                    'city': hospital.city or '',
                    'address': hospital.address or '',
                    'phone': hospital.user.phone_number or '',
                    'email': hospital.user.email,
                    'emergency_services': hospital.emergency_services,
                    'about': Truncator(hospital.about).chars(200) if hospital.about else '',
                })
            
            return JsonResponse({
                'hospitals': hospitals_data,
                'total_count': total_count,
                'page': page,
                'total_pages': total_pages,
                'status': 'success'
            })
        except Exception as e:
            logger.error(f"Error fetching hospitals: {str(e)}")
            return JsonResponse({
                'error': str(e),
                'status': 'error'
            }, status=500)
    
    def get_unique_locations(self, request):
        try:
            location_type = request.GET.get('type', '').strip()
            country = request.GET.get('country', '').strip()
            state = request.GET.get('state', '').strip()
            
            if not location_type:
                return JsonResponse({'error': 'Location type is required'}, status=400)
            
            query = HospitalClinicProfile.objects.filter(
                user__is_verified=True,
                user__is_active=True,
                user__is_deleted=False
            ).distinct()
            
            locations = []
            
            if location_type == 'country':
                countries = query.values_list('country', flat=True).distinct().order_by('country')
                locations = [c for c in countries if c]
            elif location_type == 'state':
                if country:
                    query = query.filter(country__iexact=country)
                    states = query.values_list('state', flat=True).distinct().order_by('state')
                    locations = [s for s in states if s]
            elif location_type == 'city':
                if state:
                    query = query.filter(state__iexact=state)
                if country:
                    query = query.filter(country__iexact=country)
                cities = query.values_list('city', flat=True).distinct().order_by('city')
                locations = [c for c in cities if c]
            
            return JsonResponse({
                'locations': locations,
                'status': 'success'
            })
        except Exception as e:
            logger.error(f"Error fetching locations: {str(e)}")
            return JsonResponse({
                'error': str(e),
                'status': 'error'
            }, status=500)


class FindHospitalsListingView(View):
    def get(self, request):
        hospital_id = request.GET.get('hospital_id', '')
        country = request.GET.get('country', '')
        state = request.GET.get('state', '')
        city = request.GET.get('city', '')
        page = int(request.GET.get('page', 1))
        
        hospitals = HospitalClinicProfile.objects.filter(
            user__is_verified=True,
            user__is_active=True,
            user__is_deleted=False
        ).order_by('name')
        
        context = {
            'hospital_id': hospital_id,
            'hospitals': hospitals,
            'country': country,
            'state': state,
            'city': city,
            'page': page,
        }
        return render(request, 'symptoms/find_hospitals.html', context)


def services(request):
    return render(request, 'services/services.html')