from django.core.management.base import BaseCommand
from symptoms.models import BodyPart, Symptom, Illness, IllnessSymptom
from accounts.models import Specialization
import os
from django.conf import settings

class Command(BaseCommand):
    help = 'Populate database with sample symptom and illness data'

    def handle(self, *args, **options):
        self.stdout.write('Starting to populate symptom data...')
        
        # Create Body Parts
        body_parts_data = [
            {'name': 'Head', 'description': 'Head and brain related symptoms'},
            {'name': 'Chest', 'description': 'Chest and heart related symptoms'},
            {'name': 'Abdomen', 'description': 'Stomach and digestive system'},
            {'name': 'Arms', 'description': 'Arm and hand related symptoms'},
            {'name': 'Legs', 'description': 'Leg and foot related symptoms'},
            {'name': 'Back', 'description': 'Back and spine related symptoms'},
            {'name': 'Throat', 'description': 'Throat and neck related symptoms'},
            {'name': 'Eyes', 'description': 'Eye and vision related symptoms'},
            {'name': 'Ears', 'description': 'Ear and hearing related symptoms'},
            {'name': 'Skin', 'description': 'Skin related symptoms'},
        ]
        
        body_parts = {}
        for data in body_parts_data:
            bp, created = BodyPart.objects.get_or_create(
                name=data['name'],
                defaults={'description': data['description']}
            )
            body_parts[data['name']] = bp
            self.stdout.write(f'{"Created" if created else "Found"} body part: {data["name"]}')

        # Create Symptoms
        symptoms_data = [
            {'name': 'Headache', 'body_parts': ['Head'], 'description': 'Pain in the head'},
            {'name': 'Fever', 'body_parts': ['Head'], 'description': 'Elevated body temperature'},
            {'name': 'Cough', 'body_parts': ['Throat', 'Chest'], 'description': 'Expulsion of air from lungs'},
            {'name': 'Chest Pain', 'body_parts': ['Chest'], 'description': 'Pain in chest area'},
            {'name': 'Stomach Pain', 'body_parts': ['Abdomen'], 'description': 'Pain in stomach area'},
            {'name': 'Nausea', 'body_parts': ['Abdomen'], 'description': 'Feeling of sickness'},
            {'name': 'Back Pain', 'body_parts': ['Back'], 'description': 'Pain in back'},
            {'name': 'Joint Pain', 'body_parts': ['Arms', 'Legs'], 'description': 'Pain in joints'},
            {'name': 'Sore Throat', 'body_parts': ['Throat'], 'description': 'Pain in throat'},
            {'name': 'Shortness of Breath', 'body_parts': ['Chest'], 'description': 'Difficulty breathing'},
            {'name': 'Dizziness', 'body_parts': ['Head'], 'description': 'Feeling lightheaded'},
            {'name': 'Fatigue', 'body_parts': ['Head'], 'description': 'Extreme tiredness'},
            {'name': 'Blurred Vision', 'body_parts': ['Eyes'], 'description': 'Blurry eyesight'},
            {'name': 'Rash', 'body_parts': ['Skin'], 'description': 'Skin irritation'},
            {'name': 'Ear Pain', 'body_parts': ['Ears'], 'description': 'Pain in ears'},
            {'name': 'Runny Nose', 'body_parts': ['Head'], 'description': 'Nasal discharge'},
            {'name': 'Muscle Aches', 'body_parts': ['Arms', 'Legs', 'Back'], 'description': 'Pain in muscles'},
            {'name': 'Chills', 'body_parts': ['Head'], 'description': 'Feeling cold with shivering'},
        ]
        
        symptoms = {}
        for data in symptoms_data:
            symptom, created = Symptom.objects.get_or_create(
                name=data['name'],
                defaults={
                    'description': data['description'],
                    'common_causes': 'Various causes'
                }
            )
            for bp_name in data['body_parts']:
                symptom.body_parts.add(body_parts[bp_name])
            symptoms[data['name']] = symptom
            self.stdout.write(f'{"Created" if created else "Found"} symptom: {data["name"]}')

        # Create Specializations (if they don't exist)
        specializations_data = [
            {'name': 'General Medicine'},
            {'name': 'Cardiology'},
            {'name': 'Gastroenterology'},
            {'name': 'Orthopedics'},
            {'name': 'Neurology'},
            {'name': 'Pulmonology'},
            {'name': 'Dermatology'},
            {'name': 'ENT'},
        ]
        
        specializations = {}
        for data in specializations_data:
            spec, created = Specialization.objects.get_or_create(name=data['name'])
            specializations[data['name']] = spec
            self.stdout.write(f'{"Created" if created else "Found"} specialization: {data["name"]}')

        # Create Illnesses with symptoms and severity weights
        illnesses_data = [
            {
                'name': 'Common Cold',
                'description': 'Viral infection of the upper respiratory tract causing runny nose, sore throat, and cough.',
                'severity': 'low',
                'specializations': ['General Medicine'],
                'treatment_advice': 'Rest, hydration, over-the-counter cold medicine',
                'when_to_see_doctor': 'If symptoms persist for more than 10 days or worsen',
                'symptoms': [
                    ('Cough', 0.3, 0.6, 0.9),
                    ('Sore Throat', 0.4, 0.7, 0.9),
                    ('Runny Nose', 0.5, 0.8, 0.9),
                    ('Headache', 0.2, 0.4, 0.7),
                    ('Fever', 0.1, 0.3, 0.6),
                ]
            },
            {
                'name': 'Influenza (Flu)',
                'description': 'Viral infection affecting respiratory system with fever, body aches, and fatigue.',
                'severity': 'medium',
                'specializations': ['General Medicine', 'Pulmonology'],
                'treatment_advice': 'Rest, fluids, antiviral medication if early',
                'when_to_see_doctor': 'If breathing difficulties or high fever persists',
                'symptoms': [
                    ('Fever', 0.4, 0.8, 1.0),
                    ('Cough', 0.3, 0.6, 0.9),
                    ('Headache', 0.3, 0.6, 0.8),
                    ('Fatigue', 0.4, 0.7, 0.9),
                    ('Muscle Aches', 0.3, 0.6, 0.9),
                    ('Chills', 0.2, 0.5, 0.8),
                ]
            },
            {
                'name': 'Gastroenteritis',
                'description': 'Inflammation of the stomach and intestines causing nausea, vomiting, and diarrhea.',
                'severity': 'medium',
                'specializations': ['Gastroenterology'],
                'treatment_advice': 'Hydration, bland diet, rest',
                'when_to_see_doctor': 'If unable to keep fluids down or signs of dehydration',
                'symptoms': [
                    ('Stomach Pain', 0.5, 0.8, 1.0),
                    ('Nausea', 0.4, 0.7, 0.9),
                    ('Fever', 0.2, 0.4, 0.7),
                ]
            },
            {
                'name': 'Migraine',
                'description': 'Severe headache often accompanied by nausea and sensitivity to light.',
                'severity': 'medium',
                'specializations': ['Neurology'],
                'treatment_advice': 'Rest in dark room, pain medication, avoid triggers',
                'when_to_see_doctor': 'If headaches are frequent or severe',
                'symptoms': [
                    ('Headache', 0.6, 0.9, 1.0),
                    ('Nausea', 0.3, 0.5, 0.7),
                    ('Dizziness', 0.2, 0.4, 0.6),
                ]
            },
            {
                'name': 'Bronchitis',
                'description': 'Inflammation of the bronchial tubes causing persistent cough.',
                'severity': 'medium',
                'specializations': ['Pulmonology'],
                'treatment_advice': 'Rest, hydration, cough medicine',
                'when_to_see_doctor': 'If cough lasts more than 3 weeks or breathing difficulties',
                'symptoms': [
                    ('Cough', 0.5, 0.8, 1.0),
                    ('Shortness of Breath', 0.2, 0.5, 0.8),
                    ('Fatigue', 0.2, 0.4, 0.6),
                    ('Fever', 0.1, 0.3, 0.5),
                ]
            },
        ]
        
        for data in illnesses_data:
            illness, created = Illness.objects.get_or_create(
                name=data['name'],
                defaults={
                    'description': data['description'],
                    'severity': data['severity'],
                    'treatment_advice': data['treatment_advice'],
                    'when_to_see_doctor': data['when_to_see_doctor']
                }
            )
            
            # Add specializations
            for spec_name in data['specializations']:
                illness.specializations.add(specializations[spec_name])
            
            # Add symptoms with severity weights
            for symptom_name, low_weight, mid_weight, high_weight in data['symptoms']:
                IllnessSymptom.objects.get_or_create(
                    illness=illness,
                    symptom=symptoms[symptom_name],
                    defaults={
                        'low_severity_weight': low_weight,
                        'mid_severity_weight': mid_weight,
                        'high_severity_weight': high_weight
                    }
                )
            
            self.stdout.write(f'{"Created" if created else "Found"} illness: {data["name"]}')

        self.stdout.write(
            self.style.SUCCESS('Successfully populated symptom data!')
        )