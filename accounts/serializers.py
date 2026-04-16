from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
from .models import CustomUser, PatientProfile, OTP, HospitalClinicProfile, DoctorProfile, Specialization


class PatientRegistrationSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(write_only=True)
    date_of_birth = serializers.DateField(write_only=True)
    gender = serializers.CharField(write_only=True) 
    address = serializers.CharField(write_only=True)
    contact_number = serializers.CharField(write_only=True) 

    #  OPTIONAL FIELDS
    emergency_contact = serializers.CharField(write_only=True, required=False, allow_blank=True)
    blood_group = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = CustomUser
        fields = [
            "email", "contact_number", "password",
            "full_name", "date_of_birth", "gender", "address", "emergency_contact", "blood_group"
        ]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        full_name = validated_data.pop("full_name")
        dob = validated_data.pop("date_of_birth")
        gender = validated_data.pop("gender")
        address = validated_data.pop("address")
        phone_number = validated_data.pop("contact_number")

        emergency_contact = validated_data.pop("emergency_contact", "")
        blood_group = validated_data.pop("blood_group", "")

        # normalize gender input
        gender_map = {"male": "M", "female": "F", "other": "O"}
        gender_code = gender_map.get(gender.lower(), gender[0].upper())

        user = CustomUser.objects.create_user(
            email=validated_data["email"],
            phone_number=phone_number,
            password=validated_data["password"],
            user_type="patient",
            is_deleted=True,
            is_active=False
        )
        user.set_password(validated_data['password'])
        user.save()

        PatientProfile.objects.create(
            user=user,
            full_name=full_name,
            date_of_birth=dob,
            gender=gender_code,
            address=address,
            emergency_contact=emergency_contact,
            blood_group=blood_group,
        )

        return user



class HospitalRegistrationSerializer(serializers.ModelSerializer):
    # required hospital fields
    name = serializers.CharField(write_only=True)
    established_year = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    registration_number = serializers.CharField(write_only=True, required=False, allow_blank=True)
    gst_number = serializers.CharField(write_only=True, required=False, allow_blank=True)
    about = serializers.CharField(write_only=True, required=False, allow_blank=True)

    # plain string fields (no FK now)
    country = serializers.CharField(write_only=True, required=False, allow_blank=True)
    state = serializers.CharField(write_only=True, required=False, allow_blank=True)
    city = serializers.CharField(write_only=True, required=False, allow_blank=True)
    address = serializers.CharField(write_only=True, required=False, allow_blank=True)
    pincode = serializers.CharField(write_only=True, required=False, allow_blank=True)
    website = serializers.URLField(write_only=True, required=False, allow_blank=True)

    medical_equipments = serializers.CharField(write_only=True, required=False, allow_blank=True)
    facilities = serializers.CharField(write_only=True, required=False, allow_blank=True)
    emergency_services = serializers.BooleanField(write_only=True, required=False)

    contact_number = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = [
            "email", "contact_number", "password",
            "name", "established_year", "registration_number", "gst_number", "about",
            "country", "state", "city", "address", "pincode", "website",
            "medical_equipments", "facilities", "emergency_services"
        ]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        # pop common fields
        name = validated_data.pop("name")
        phone_number = validated_data.pop("contact_number")
        password = validated_data.pop("password")

        # optional fields
        established_year = validated_data.pop("established_year", None)
        registration_number = validated_data.pop("registration_number", "")
        gst_number = validated_data.pop("gst_number", "")
        about = validated_data.pop("about", "")

        country = validated_data.pop("country", "")
        state = validated_data.pop("state", "")
        city = validated_data.pop("city", "")
        address = validated_data.pop("address", "")
        pincode = validated_data.pop("pincode", "")
        website = validated_data.pop("website", "")

        medical_equipments = validated_data.pop("medical_equipments", "")
        facilities = validated_data.pop("facilities", "")
        emergency_services = validated_data.pop("emergency_services", False)

        # Create user (inactive until OTP verification)
        user = CustomUser.objects.create_user(
            email=validated_data["email"],
            phone_number=phone_number,
            password=password,
            user_type="hospital",
            is_deleted=True,
            is_active=False,
        )
        user.set_password(password)
        user.save()

        # Create HospitalClinicProfile
        HospitalClinicProfile.objects.create(
            user=user,
            name=name,
            established_year=established_year,
            registration_number=registration_number,
            gst_number=gst_number,
            about=about,
            country=country,
            state=state,
            city=city,
            address=address,
            pincode=pincode,
            website=website,
            medical_equipments=medical_equipments,
            facilities=facilities,
            emergency_services=bool(emergency_services),
        )

        return user


class DoctorRegistrationSerializer(serializers.ModelSerializer):
    # Doctor-specific fields
    doctor_name = serializers.CharField(write_only=True)
    education = serializers.CharField(write_only=True, required=False, allow_blank=True)
    experience = serializers.IntegerField(write_only=True, required=False)
    license_number = serializers.CharField(write_only=True, required=False, allow_blank=True)
    consultation_fee = serializers.DecimalField(write_only=True, max_digits=8, decimal_places=2, required=False)
    bio = serializers.CharField(write_only=True, required=False, allow_blank=True)

    country = serializers.CharField(write_only=True)
    state = serializers.CharField(write_only=True)
    city = serializers.CharField(write_only=True)
    address = serializers.CharField(write_only=True)
    pincode = serializers.CharField(write_only=True)

    languages_spoken = serializers.CharField(write_only=True, required=False, allow_blank=True)
    awards_certifications = serializers.CharField(write_only=True, required=False, allow_blank=True)

    # Auth/User fields
    email = serializers.EmailField(write_only=True)
    contact_number = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, min_length=8)

    # Relationship field
    specializations = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Specialization.objects.all(),
        required=False
    )

    class Meta:
        model = CustomUser
        fields = [
            "email", "contact_number", "password",
            "doctor_name", "education", "experience", "license_number",
            "consultation_fee", "bio",
            "country", "state", "city", "address", "pincode",
            "languages_spoken", "awards_certifications",
            "specializations",
        ]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        # pop common fields
        doctor_name = validated_data.pop("doctor_name")
        phone_number = validated_data.pop("contact_number")
        password = validated_data.pop("password")
        email = validated_data.pop("email")

        # extract optional doctor profile fields
        education = validated_data.pop("education", "")
        experience = validated_data.pop("experience", 0)
        license_number = validated_data.pop("license_number", "")
        consultation_fee = validated_data.pop("consultation_fee", 0)
        bio = validated_data.pop("bio", "")

        country = validated_data.pop("country")
        state = validated_data.pop("state")
        city = validated_data.pop("city")
        address = validated_data.pop("address")
        pincode = validated_data.pop("pincode")

        languages_spoken = validated_data.pop("languages_spoken", "")
        awards_certifications = validated_data.pop("awards_certifications", "")

        specializations = validated_data.pop("specializations", [])

        # Create user (inactive until OTP verification)
        user = CustomUser.objects.create_user(
            email=email,
            phone_number=phone_number,
            password=password,
            user_type="doctor",
            is_deleted=True,
            is_active=False,
        )
        user.set_password(password)  # ensure password is hashed
        user.save()

        # Create DoctorProfile
        doctor = DoctorProfile.objects.create(
            user=user,
            doctor_name=doctor_name,
            education=education,
            experience=experience,
            license_number=license_number,
            consultation_fee=consultation_fee,
            bio=bio,
            country=country,
            state=state,
            city=city,
            address=address,
            pincode=pincode,
            languages_spoken=languages_spoken,
            awards_certifications=awards_certifications,
        )

        # Add ManyToMany specializations
        if specializations:
            doctor.specializations.set(specializations)

        return user


class DoctorWorkingHoursSerializer(serializers.Serializer):
    """
    Serializer for managing doctor's weekly working hours.
    Handles all 7 days in a single request.
    """
    working_hours = serializers.SerializerMethodField()

    def get_working_hours(self, obj):
        """Get all 7 days of working hours"""
        from .models import DoctorWorkingHours
        
        if isinstance(obj, dict):
            # When creating/updating, obj is the validated data
            return obj.get('working_hours', [])
        
        # When retrieving, fetch from database
        days = DoctorWorkingHours.objects.filter(doctor=obj).order_by('day_of_week')
        return [
            {
                'day_of_week': day.day_of_week,
                'day_name': day.get_day_of_week_display(),
                'start_time': day.start_time.isoformat() if day.start_time else None,
                'end_time': day.end_time.isoformat() if day.end_time else None,
                'is_off': day.is_off,
            }
            for day in days
        ]


class DoctorWorkingHoursDetailSerializer(serializers.ModelSerializer):
    """Serializer for individual working hours record"""
    day_name = serializers.CharField(source='get_day_of_week_display', read_only=True)
    
    class Meta:
        from .models import DoctorWorkingHours
        model = DoctorWorkingHours
        fields = ['id', 'day_of_week', 'day_name', 'start_time', 'end_time', 'is_off']
        read_only_fields = ['id', 'day_name']


# -------------------- Appointment Serializers --------------------
from .models import Appointment


class AppointmentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new appointments by patients"""
    doctor_id = serializers.IntegerField(write_only=True, required=False)
    hospital_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = Appointment
        fields = ['doctor_id', 'hospital_id', 'appointment_date', 'patient_message']
    
    def validate_appointment_date(self, value):
        """
        Ensure appointment date is not in the past.
        Update: Same-day booking is now allowed (2026-02-22).
        Previous restriction is commented out below.
        """
        from django.utils import timezone
        today = timezone.now().date()
        
        if value < today:
            raise serializers.ValidationError("Appointment date cannot be in the past.")
        
        # --- Same-day booking restriction removed ---
        # if value == today:
        #     raise serializers.ValidationError(
        #         "Same-day appointments are not available. Please select a date starting from tomorrow to allow proper scheduling and preparation."
        #     )
        # Now allowing same-day bookings for improved flexibility and user experience.
        
        # Restrict to max 60 days in future
        max_future_date = today + timedelta(days=60)
        if value > max_future_date:
            raise serializers.ValidationError("Appointment date cannot be more than 60 days in the future.")
        
        return value
    
    def validate(self, attrs):
        """Additional validations"""
        request = self.context.get('request')
        
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("User must be authenticated.")
        
        if request.user.user_type != 'patient':
            raise serializers.ValidationError("Only patients can create appointments.")
        
        # Ensure either doctor_id or hospital_id is provided (but not both)
        doctor_id = attrs.get('doctor_id')
        hospital_id = attrs.get('hospital_id')
        
        if not doctor_id and not hospital_id:
            raise serializers.ValidationError("Either doctor_id or hospital_id must be provided.")
        
        if doctor_id and hospital_id:
            raise serializers.ValidationError("Cannot book appointment with both doctor and hospital. Please choose one.")
        
        # Handle doctor appointment validation
        if doctor_id:
            try:
                doctor = DoctorProfile.objects.get(id=doctor_id)
            except DoctorProfile.DoesNotExist:
                raise serializers.ValidationError("Invalid doctor ID.")
            
            # Check if doctor is available for appointments
            if not doctor.is_available:
                raise serializers.ValidationError(
                    "This doctor is currently unavailable for appointments. Please try again later or choose another doctor."
                )
            
            # Check if appointment date falls on doctor's off day
            appointment_date = attrs.get('appointment_date')
            day_of_week = appointment_date.weekday()  # Monday=0, Sunday=6
            
            from .models import DoctorWorkingHours
            try:
                working_hour = DoctorWorkingHours.objects.get(doctor=doctor, day_of_week=day_of_week)
                if working_hour.is_off:
                    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                    raise serializers.ValidationError(
                        f"The selected doctor is not available on {day_names[day_of_week]}s. Please choose a different date when the doctor is available."
                    )
            except DoctorWorkingHours.DoesNotExist:
                # If no working hours set, allow booking (optional approach)
                pass
            
            # Prevent duplicate pending doctor appointments
            try:
                patient = request.user.patient_profile
                appointment_date = attrs.get('appointment_date')
                
                duplicate = Appointment.objects.filter(
                    patient=patient,
                    doctor=doctor,
                    appointment_date=appointment_date,
                    status='PENDING'
                ).exists()
                
                if duplicate:
                    raise serializers.ValidationError(
                        "You already have a pending appointment with this doctor on this date."
                    )
            except PatientProfile.DoesNotExist:
                raise serializers.ValidationError("Patient profile not found.")
        
        # Handle hospital appointment validation
        if hospital_id:
            from .models import HospitalClinicProfile
            try:
                hospital = HospitalClinicProfile.objects.get(id=hospital_id)
            except HospitalClinicProfile.DoesNotExist:
                raise serializers.ValidationError("Invalid hospital ID.")
            
            # Check if hospital is active
            if not hospital.user.is_active or not hospital.user.is_verified:
                raise serializers.ValidationError(
                    "This hospital is currently unavailable for appointments. Please try again later or choose another hospital."
                )
            
            # Prevent duplicate pending hospital appointments
            try:
                patient = request.user.patient_profile
                appointment_date = attrs.get('appointment_date')
                
                duplicate = Appointment.objects.filter(
                    patient=patient,
                    hospital=hospital,
                    appointment_date=appointment_date,
                    status='PENDING'
                ).exists()
                
                if duplicate:
                    raise serializers.ValidationError(
                        "You already have a pending appointment with this hospital on this date."
                    )
            except PatientProfile.DoesNotExist:
                raise serializers.ValidationError("Patient profile not found.")
        
        return attrs
    
    def create(self, validated_data):
        """Create appointment"""
        request = self.context.get('request')
        doctor_id = validated_data.pop('doctor_id', None)
        hospital_id = validated_data.pop('hospital_id', None)
        
        patient = request.user.patient_profile
        
        # Create appointment with either doctor or hospital
        if doctor_id:
            doctor = DoctorProfile.objects.get(id=doctor_id)
            appointment = Appointment.objects.create(
                patient=patient,
                doctor=doctor,
                **validated_data
            )
        else:  # hospital_id
            from .models import HospitalClinicProfile
            hospital = HospitalClinicProfile.objects.get(id=hospital_id)
            appointment = Appointment.objects.create(
                patient=patient,
                hospital=hospital,
                **validated_data
            )
        
        return appointment


class AppointmentListSerializer(serializers.ModelSerializer):
    """Serializer for listing appointments with full details"""
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    patient_phone = serializers.CharField(source='patient.user.phone_number', read_only=True)
    patient_address = serializers.CharField(source='patient.address', read_only=True)
    patient_email = serializers.EmailField(source='patient.user.email', read_only=True)
    
    doctor_name = serializers.SerializerMethodField()
    doctor_specializations = serializers.SerializerMethodField()
    doctor_phone = serializers.SerializerMethodField()
    
    hospital_name = serializers.SerializerMethodField()
    hospital_phone = serializers.SerializerMethodField()
    hospital_address = serializers.SerializerMethodField()
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    appointment_type = serializers.SerializerMethodField()
    
    class Meta:
        model = Appointment
        fields = [
            'id', 'patient_name', 'patient_phone', 'patient_address', 'patient_email',
            'doctor_name', 'doctor_specializations', 'doctor_phone',
            'hospital_name', 'hospital_phone', 'hospital_address',
            'appointment_date', 'patient_message', 'status', 'status_display',
            'appointment_type', 'doctor_provided_time', 'rejection_reason', 'cancellation_reason',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'patient_name', 'patient_phone', 'patient_address', 'patient_email',
            'doctor_name', 'doctor_specializations', 'doctor_phone',
            'hospital_name', 'hospital_phone', 'hospital_address',
            'appointment_type', 'status_display', 'created_at', 'updated_at'
        ]
    
    def get_appointment_type(self, obj):
        """Get appointment type: 'doctor' or 'hospital'"""
        if obj.doctor:
            return 'doctor'
        elif obj.hospital:
            return 'hospital'
        return 'unknown'
    
    def get_doctor_name(self, obj):
        """Get doctor name if appointment is with doctor"""
        if obj.doctor:
            return obj.doctor.doctor_name
        return None
    
    def get_doctor_phone(self, obj):
        """Get doctor phone if appointment is with doctor"""
        if obj.doctor:
            return obj.doctor.user.phone_number
        return None
    
    def get_doctor_specializations(self, obj):
        """Get doctor specializations as list"""
        if obj.doctor:
            return [spec.name for spec in obj.doctor.specializations.all()]
        return []
    
    def get_hospital_name(self, obj):
        """Get hospital name if appointment is with hospital"""
        if obj.hospital:
            return obj.hospital.name
        return None
    
    def get_hospital_phone(self, obj):
        """Get hospital phone if appointment is with hospital"""
        if obj.hospital:
            return obj.hospital.user.phone_number
        return None
    
    def get_hospital_address(self, obj):
        """Get hospital address if appointment is with hospital"""
        if obj.hospital:
            return obj.hospital.address
        return None


class AppointmentAcceptSerializer(serializers.Serializer):
    """Serializer for doctor accepting an appointment"""
    doctor_provided_time = serializers.TimeField(required=True)
    
    def validate(self, attrs):
        """Validate acceptance"""
        appointment = self.context.get('appointment')
        
        if not appointment:
            raise serializers.ValidationError("Appointment not found.")
        
        if appointment.status != 'PENDING':
            raise serializers.ValidationError("Only pending appointments can be accepted.")
        
        return attrs


class AppointmentRejectSerializer(serializers.Serializer):
    """Serializer for doctor rejecting an appointment"""
    rejection_reason = serializers.CharField(required=True, min_length=10)
    
    def validate(self, attrs):
        """Validate rejection"""
        appointment = self.context.get('appointment')
        
        if not appointment:
            raise serializers.ValidationError("Appointment not found.")
        
        if appointment.status != 'PENDING':
            raise serializers.ValidationError("Only pending appointments can be rejected.")
        
        return attrs


class AppointmentCancelSerializer(serializers.Serializer):
    """Serializer for patient canceling an appointment"""
    cancellation_reason = serializers.CharField(required=True, min_length=10)
    
    def validate(self, attrs):
        """Validate cancellation"""
        appointment = self.context.get('appointment')
        
        if not appointment:
            raise serializers.ValidationError("Appointment not found.")
        
        if appointment.status != 'PENDING':
            raise serializers.ValidationError("Only pending appointments can be canceled.")
        
        return attrs