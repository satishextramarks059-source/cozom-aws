# Healthcare Django Project - Complete Architecture Analysis

**Project Name:** COZOM Healthcare System  
**Analysis Date:** February 21, 2026  
**Django Version:** 5.2.6  
**Database:** PostgreSQL  
**API Framework:** Django REST Framework 3.16.1

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Project Architecture Overview](#project-architecture-overview)
3. [Technology Stack](#technology-stack)
4. [Folder & File Structure](#folder--file-structure)
5. [Application Responsibilities](#application-responsibilities)
6. [Data Models & Entity Relationships](#data-models--entity-relationships)
7. [Request → Response Flow](#request--response-flow)
8. [Authentication & Authorization](#authentication--authorization)
9. [Business Logic Layer](#business-logic-layer)
10. [API Endpoints](#api-endpoints)
11. [Templates & Frontend Architecture](#templates--frontend-architecture)
12. [Middleware & Signals](#middleware--signals)
13. [Database Design & Schema](#database-design--schema)
14. [External Integrations](#external-integrations)
15. [Security Practices](#security-practices)
16. [Performance Considerations](#performance-considerations)
17. [Code Quality Assessment](#code-quality-assessment)
18. [Existing Features Analysis](#existing-features-analysis)
19. [Appointment Booking System Requirements](#appointment-booking-system-requirements)

---

## 1. Executive Summary

COZOM is a comprehensive healthcare management platform built with Django that facilitates connections between patients, doctors, and hospitals. The platform features:

- **Multi-role user system** (Patient, Doctor, Hospital, Admin, Staff)
- **Symptom checker with AI-powered diagnosis**
- **Doctor discovery and recommendation system**
- **Location-based doctor filtering**
- **Subscription management**
- **Blog system**
- **Feedback and contact management**

**Key Highlights:**
- Modern REST API architecture using DRF
- PostgreSQL database with optimized indexing
- Responsive frontend with Bootstrap 5
- Signal-based event handling
- OTP-based email verification
- Role-based access control

---

## 2. Project Architecture Overview

### Architecture Pattern
The project follows a **monolithic Django architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────┐
│                     Frontend Layer                       │
│  (Templates + Bootstrap + Vanilla JS + jQuery)          │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                    URL Routing Layer                     │
│         (Django URLConf + Path Routing)                 │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                  View/Controller Layer                   │
│    (Function-based Views + Class-based Views/APIs)     │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                  Business Logic Layer                    │
│  (Models, Serializers, Forms, Signals, Utils)          │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                      Data Layer                          │
│              (Django ORM + PostgreSQL)                   │
└─────────────────────────────────────────────────────────┘
```

### Application Structure
- **Modular app design**: Each feature is encapsulated in Django apps
- **RESTful API endpoints**: For AJAX-based interactions
- **Template-based rendering**: For page loads
- **Hybrid approach**: Mix of traditional Django views and API views

---

## 3. Technology Stack

### Backend
| Component | Technology | Version |
|-----------|-----------|---------|
| Framework | Django | 5.2.6 |
| API Framework | Django REST Framework | 3.16.1 |
| Database | PostgreSQL | - |
| DB Driver | psycopg2-binary | 2.9.10 |
| WSGI Server | Built-in (Production: likely Gunicorn) | - |
| ASGI Support | Yes (asgi.py configured) | - |

### Frontend
| Component | Technology |
|-----------|-----------|
| CSS Framework | Bootstrap 5 |
| Icons | Font Awesome 5.10, Bootstrap Icons |
| JavaScript | Vanilla JS (ES6+) |
| AJAX | Fetch API |
| Animations | WOW.js, Animate.css |
| Carousel | Owl Carousel |
| Rich Text Editor | CKEditor 5 |

### DevOps/Infrastructure
| Component | Technology |
|-----------|-----------|
| Environment Management | django-environ |
| CORS Handling | django-cors-headers |
| Image Processing | Pillow |
| Static Files | Django Static Files |
| Media Files | Django Media Files |

---

## 4. Folder & File Structure

```
cozom/                          # Root project directory
├── manage.py                   # Django management script
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (not in repo)
│
├── cozom/                      # Main project package
│   ├── __init__.py
│   ├── settings.py             # Project settings
│   ├── urls.py                 # Root URL configuration
│   ├── wsgi.py                 # WSGI entry point
│   └── asgi.py                 # ASGI entry point
│
├── accounts/                   # User management app
│   ├── models.py               # User, Profile, Subscription models
│   ├── views.py                # Authentication, dashboards
│   ├── serializers.py          # DRF serializers
│   ├── forms.py                # Django forms
│   ├── urls.py                 # App-specific URLs
│   ├── admin.py                # Admin customizations
│   ├── signals.py              # Post-save signals for profiles
│   ├── context_processors.py  # Custom context data
│   ├── email_utils.py          # Email sending utilities
│   └── migrations/             # Database migrations
│
├── symptoms/                   # Symptom checker & doctor discovery
│   ├── models.py               # BodyPart, Symptom, Illness models
│   ├── views.py                # Symptom checker, doctor listing
│   ├── urls.py                 # App-specific URLs
│   ├── admin.py                # Admin customizations
│   ├── management/
│   │   └── commands/
│   │       └── populate_symptom_data.py  # Data seeding
│   └── migrations/
│
├── blog/                       # Blog management
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── forms.py
│   └── migrations/
│
├── templates/                  # Django templates
│   ├── base.html               # Base layout
│   ├── home.html               # Landing page
│   ├── accounts/               # User-related templates
│   │   ├── login.html
│   │   ├── patient-signup.html
│   │   ├── doctor-signup.html
│   │   ├── hospital-signup.html
│   │   ├── patient-dashboard.html
│   │   └── doctor-dashboard.html
│   ├── admin-user/             # Admin templates
│   ├── symptoms/               # Symptom checker templates
│   │   ├── symptom_checks.html
│   │   ├── recommended_doctor_listing.html
│   │   └── registered_doctors_listing.html
│   ├── blog/
│   └── contacts/
│
├── static/                     # Static assets
│   ├── css/
│   │   ├── bootstrap.min.css
│   │   └── style.css
│   ├── js/
│   │   ├── registered-doctor-listing.js
│   │   ├── recommended-doctor-listing.js
│   │   ├── doctor-dashboard.js
│   │   ├── patient-dashboard.js
│   │   └── [other feature-specific JS]
│   ├── img/
│   └── lib/                    # Third-party libraries
│       ├── animate/
│       ├── owlcarousel/
│       ├── wow/
│       └── waypoints/
│
├── media/                      # User-uploaded files
│   ├── blog/
│   │   ├── images/
│   │   └── thumbnails/
│   ├── body_parts/
│   │   └── icons/
│   └── subscriptions/
│       └── qr/
│
├── logs/                       # Application logs
└── env/                        # Virtual environment (not in repo)
```

---

## 5. Application Responsibilities

### 5.1 accounts/ App

**Primary Responsibility:** User management, authentication, profiles, and subscriptions

**Key Features:**
- Custom user model with 5 user types (patient, doctor, hospital, admin, staff)
- User registration with OTP verification
- Password reset functionality
- Role-specific profiles (PatientProfile, DoctorProfile, HospitalClinicProfile)
- Doctor working hours management
- Subscription plan management
- Contact and feedback systems
- Admin dashboard for user management

**Models:**
- `CustomUser` - Core user model (extends AbstractBaseUser)
- `PatientProfile` - Patient-specific data
- `DoctorProfile` - Independent doctor information
- `HospitalClinicProfile` - Hospital/clinic information
- `HospitalDoctors` - Many-to-many relationship for hospital-employed doctors
- `DoctorWorkingHours` - Doctor availability schedule
- `Specialization` - Medical specialties
- `OTP` - Email/phone verification codes
- `SubscriptionPlan` - Subscription offerings
- `UserSubscription` - User-plan associations
- `ContactMessage` - Contact form submissions
- `Feedback` - User feedback

**API Endpoints:**
- Registration APIs (Patient, Doctor, Hospital)
- OTP verification and resend
- Login/logout
- Password reset flow
- Dashboard data retrieval
- Doctor availability toggle
- Working hours CRUD

### 5.2 symptoms/ App

**Primary Responsibility:** Symptom checking, illness prediction, and doctor recommendations

**Key Features:**
- Interactive symptom checker with body part selection
- AI-powered illness diagnosis (mock implementation)
- Probability-based illness matching
- Specialist doctor recommendations
- Location-based doctor filtering (Country → State → City)
- Doctor listing with pagination
- Conditional cascading location filters

**Models:**
- `BodyPart` - Anatomical body parts with icons
- `Symptom` - Medical symptoms
- `Illness` - Diseases with specializations
- `IllnessSymptom` - Symptom-illness relationships with severity weights
- `SymptomCheckSession` - User symptom check sessions
- `SelectedSymptom` - User-selected symptoms with severity
- `SymptomCheckResult` - Calculated illness probabilities

**API Endpoints:**
- Symptom checker API (multi-step process)
- Doctors by specialist API
- Registered doctors API with location filtering
- Location dropdown population API (dynamic country/state/city)

**Views:**
- `SymptomCheckView` - Symptom checker page
- `RecommendedDoctorListingView` - Post-diagnosis doctor listing
- `RegisteredDoctorsListingView` - General doctor search

### 5.3 blog/ App

**Primary Responsibility:** Content management system

**Key Features:**
- Blog post creation and management
- Rich text editing with CKEditor
- Image uploads
- Blog listing and detail views

---

## 6. Data Models & Entity Relationships

### 6.1 User & Profile Models

```
┌─────────────────────┐
│    CustomUser       │
├─────────────────────┤
│ email (unique)      │
│ phone_number        │
│ user_type           │◄──────┐
│ is_verified         │       │
│ is_active           │       │
│ is_deleted (soft)   │       │
│ username            │       │
└─────────────────────┘       │
         △                     │
         │                     │
         │ OneToOne            │
    ┌────┴──────┬──────────┐  │
    │           │          │  │
┌───▼──────┐ ┌─▼─────────┐ ┌─▼────────────┐
│Patient   │ │Doctor     │ │Hospital      │
│Profile   │ │Profile    │ │ClinicProfile │
├──────────┤ ├───────────┤ ├──────────────┤
│full_name │ │doctor_name│ │name          │
│dob       │ │education  │ │registration  │
│gender    │ │experience │ │country       │
│address   │ │country    │ │state         │
│blood_grp │ │state      │ │city          │
└──────────┘ │city       │ │facilities    │
             │license_no │ │emergency_svc │
             │consult_fee│ └──────────────┘
             │rating_avg │        │
             │num_reviews│        │
             └───────────┘        │
                  │               │
                  │M2M            │
                  ▼               │
           ┌──────────────┐       │
           │Specialization│       │
           ├──────────────┤       │
           │name          │       │
           │description   │       │
           │icon          │       │
           └──────────────┘       │
                  △               │
                  │               │
                  │M2M            │
                  │               │
           ┌──────┴───────┐       │
           │    Illness   │       │
           ├──────────────┤       │
           │name          │       │
           │severity      │       │
           │treatment_adv │       │
           └──────────────┘       │
                                  │
                  ┌───────────────┘
                  │
                  ▼
         ┌─────────────────┐
         │HospitalDoctors  │
         ├─────────────────┤
         │hospital_id (FK) │
         │doctor_id (FK)   │
         │joining_date     │
         │is_active        │
         └─────────────────┘
```

### 6.2 Doctor Working Hours

```
┌──────────────────────────┐
│    DoctorProfile         │
└──────────────────────────┘
            │
            │ OneToMany
            ▼
┌──────────────────────────┐
│  DoctorWorkingHours      │
├──────────────────────────┤
│ doctor_id (FK)           │
│ day_of_week (0-6)        │
│ start_time               │
│ end_time                 │
│ is_off                   │
└──────────────────────────┘
UNIQUE: (doctor, day_of_week)
```

### 6.3 Symptom Checker Flow

```
┌──────────────────────┐
│  BodyPart            │
└──────────────────────┘
         △
         │ M2M
         │
┌────────▼─────────────┐
│  Symptom             │
├──────────────────────┤
│ name                 │
│ description          │
│ common_causes        │
└──────────────────────┘
         │
         │ M2M (via IllnessSymptom)
         ▼
┌──────────────────────┐
│  Illness             │
├──────────────────────┤
│ name                 │
│ severity             │
│ treatment_advice     │
│ when_to_see_doctor   │
└──────────────────────┘
         △
         │
┌────────┴─────────────────┐
│  IllnessSymptom          │
├──────────────────────────┤
│ illness_id (FK)          │
│ symptom_id (FK)          │
│ low_severity_weight      │
│ mid_severity_weight      │
│ high_severity_weight     │
└──────────────────────────┘

User Session Flow:
┌─────────────────────────┐
│ SymptomCheckSession     │
├─────────────────────────┤
│ id (UUID)               │
│ patient_id (FK)         │
│ created_at              │
│ completed_at            │
└─────────────────────────┘
         │
         │ OneToMany
    ┌────┴────────────┐
    ▼                 ▼
┌─────────────┐  ┌────────────────┐
│Selected     │  │SymptomCheck    │
│Symptom      │  │Result          │
├─────────────┤  ├────────────────┤
│session (FK) │  │session (FK)    │
│symptom (FK) │  │illness (FK)    │
│user_severity│  │probability     │
└─────────────┘  │reasoning       │
                 └────────────────┘
```

### 6.4 Subscription System

```
┌──────────────────────┐
│  SubscriptionPlan    │
├──────────────────────┤
│ name                 │
│ user_type            │
│ monthly_price        │
│ half_yearly_discount │
│ yearly_discount      │
│ receiver_qr          │
│ is_active            │
└──────────────────────┘
         △
         │
         │ FK
         │
┌────────┴─────────────┐
│  UserSubscription    │
├──────────────────────┤
│ user_id (FK)         │
│ subscription_plan(FK)│
│ start_date           │
│ end_date             │
│ duration_in_months   │
│ final_amount_paid    │
└──────────────────────┘
```

### 6.5 Key Relationships Summary

| Relationship | Type | Description |
|--------------|------|-------------|
| CustomUser ↔ PatientProfile | OneToOne | Patient user profile |
| CustomUser ↔ DoctorProfile | OneToOne | Doctor user profile |
| CustomUser ↔ HospitalClinicProfile | OneToOne | Hospital user profile |
| DoctorProfile ↔ Specialization | ManyToMany | Doctor specialties |
| DoctorProfile ↔ DoctorWorkingHours | OneToMany | Weekly schedule (7 days) |
| HospitalClinicProfile ↔ DoctorProfile | ManyToMany (via HospitalDoctors) | Hospital-employed doctors |
| Illness ↔ Specialization | ManyToMany | Required specialist types |
| Illness ↔ Symptom | ManyToMany (via IllnessSymptom) | Disease symptoms with weights |
| SymptomCheckSession ↔ SelectedSymptom | OneToMany | User selections |
| SymptomCheckSession ↔ SymptomCheckResult | OneToMany | Calculated results |

---

## 7. Request → Response Flow

### 7.1 Traditional Page Load Flow

```
User Request
    ↓
Django URLs (cozom/urls.py → app/urls.py)
    ↓
View Function/Class
    ↓
Business Logic (Models, Forms, Utilities)
    ↓
Database Query (Django ORM)
    ↓
Context Data Preparation
    ↓
Template Rendering
    ↓
HTTP Response (HTML)
```

**Example: Doctor Signup Page**
```
GET /user/doctor-signup/
    ↓
accounts.urls → views.doctor_signup
    ↓
Specialization.objects.all()
    ↓
Context: {"specializations": [...]}
    ↓
templates/accounts/doctor-signup.html
    ↓
HTTP 200 + HTML
```

### 7.2 AJAX/API Flow

```
User Action (JavaScript)
    ↓
Fetch API Request
    ↓
Django URLs → API View (DRF or Custom)
    ↓
Serializer Validation (DRF)
    ↓
Business Logic
    ↓
Database Operations
    ↓
JSON Response
    ↓
JavaScript Handler
    ↓
DOM Update
```

**Example: Doctor Search with Filters**
```
User selects Specialization + Location
    ↓
JavaScript: fetch('/api/registered-doctors/?specialization_id=5&country=USA')
    ↓
symptoms.urls → RegisteredDoctorsAPIView.get_doctors()
    ↓
DoctorProfile.objects.filter(specializations=5, country='USA')
    ↓
Pagination + Serialization
    ↓
JsonResponse({doctors: [...], total_count: 42, ...})
    ↓
JavaScript: renderDoctorCards(data.doctors)
    ↓
DOM updated with doctor cards
```

### 7.3 Symptom Checker Flow (Multi-Step)

```
Step 1: Get Body Parts
User → GET /api/symptom-check/
     → BodyPart.objects.all()
     → JSON: {body_parts: [{id, name, icon_url}, ...]}
     → Display body part selection UI

Step 2: Get Symptoms for Body Part
User selects body part
     → POST /api/symptom-check/ {step: 'get_symptoms', body_part_id: 3}
     → Symptom.objects.filter(body_parts=3)
     → JSON: {symptoms: [...]}
     → Display symptom checklist with severity selection

Step 3: Calculate Results
User submits symptoms
     → POST /api/symptom-check/ {step: 'calculate_results', symptoms: [...]}
     → session.calculate_illness_probabilities(symptoms)
     → SymptomCheckResult.objects.create(...)
     → JSON: {results: [{illness, probability, specialist}, ...]}
     → Display results with "Find Doctor" button

Step 4: Find Specialist
User clicks "Find & Book Appointment"
     → Redirect to /recommended-doctors/?specialist_id=X&illness_name=Y
     → Load RecommendedDoctorListingView
     → Display filtered doctors
```

### 7.4 Doctor Listing Flow (Cascading Filters)

```
Initial Load:
/registered-doctors/
    ↓
RegisteredDoctorsListingView.get()
    ↓
Context: {specializations: all(), filters: {}}
    ↓
Template: registered_doctors_listing.html
    ↓
Show empty state: "Select a specialization..."

User Flow:
1. User selects Specialization
     ↓ JavaScript onChange
   Enable Country dropdown
     ↓
   fetch('/api/registered-doctors/?action=locations&type=country&specialization_id=5')
     ↓
   Populate country options
   
2. User selects Country
     ↓
   Enable State dropdown
     ↓
   fetch('/api/registered-doctors/?action=locations&type=state&specialization_id=5&country=USA')
     ↓
   Populate state options
   
3. User selects State
     ↓
   Enable City dropdown
     ↓
   fetch('/api/registered-doctors/?action=locations&type=city&specialization_id=5&country=USA&state=California')
     ↓
   Populate city options

4. User clicks Search
     ↓
   fetch('/api/registered-doctors/?specialization_id=5&country=USA&state=California&city=Los Angeles')
     ↓
   RegisteredDoctorsAPIView.get_doctors()
     ↓
   DoctorProfile.objects.filter(specializations=5, country__icontains='USA', ...)
     ↓
   JSON: {doctors: [...], total_count: 15, page: 1, total_pages: 1}
     ↓
   JavaScript: renderDoctorCards()
     ↓
   Display doctor cards with "View Details" and "Book Appointment" buttons
```

---

## 8. Authentication & Authorization

### 8.1 Authentication System

**Custom User Model:**
```python
AUTH_USER_MODEL = 'accounts.CustomUser'
```

**Authentication Methods:**
1. **Email + Password** (Primary)
   - Email is USERNAME_FIELD
   - Password hashed with Django's default (PBKDF2)

2. **Session-Based Authentication**
   - Django's built-in session middleware
   - Session data stored in database

**Registration Flow:**
```
1. User submits registration form
     ↓
2. Serializer validation
     ↓
3. CustomUser created with is_deleted=True, is_active=False
     ↓
4. Profile created (Patient/Doctor/Hospital)
     ↓
5. OTP generated and sent via email
     ↓
6. User enters OTP
     ↓
7. OTP verified → is_deleted=False
     ↓
8. Admin verification → is_active=True (for doctors/hospitals)
```

**Login Flow:**
```
1. POST /api/login/ {email, password}
     ↓
2. authenticate(email=email, password=password)
     ↓
3. Check is_active and is_deleted
     ↓
4. login(request, user)
     ↓
5. Store user data in session:
    - user_type
    - is_verified
    - is_active
    - is_staff
     ↓
6. Redirect based on user_type
```

### 8.2 Authorization & Access Control

**Role-Based Access (5 User Types):**
```python
USER_TYPES = (
    ('patient', 'Patient'),
    ('doctor', 'Doctor'),
    ('hospital', 'Hospital'),
    ('admin', 'Admin'),
    ('staff', 'Staff'),
)
```

**Access Control Mechanisms:**

1. **View-Level Decorators:**
   ```python
   @staff_member_required
   def admin_dashboard(request):
       ...
   ```

2. **Session-Based Checks:**
   ```python
   user_type = request.session.get("user_type")
   is_verified = request.session.get("is_verified")
   
   if user_type != 'doctor':
       return JsonResponse({"error": "Unauthorized"}, status=403)
   ```

3. **Template-Level Checks:**
   ```django
   {% if user.is_authenticated and user.user_type == 'doctor' %}
       <!-- Doctor-specific content -->
   {% endif %}
   ```

4. **Model-Level Properties:**
   ```python
   @property
   def is_patient(self): 
       return self.user_type == 'patient'
   ```

**Permission Matrix:**

| Feature | Patient | Doctor | Hospital | Admin | Staff |
|---------|---------|--------|----------|-------|-------|
| Register | ✓ | ✓ | ✓ | - | - |
| Login | ✓ | ✓ | ✓ | ✓ | ✓ |
| Symptom Checker | ✓ | ✓ | ✓ | - | - |
| Find Doctors | ✓ | ✓ | ✓ | - | - |
| Book Appointment | ✓ | - | - | - | - |
| Manage Appointments | - | ✓ | - | - | - |
| Working Hours | - | ✓ | - | - | - |
| User Management | - | - | - | ✓ | ✓ |
| Subscription Plans | - | - | - | ✓ | ✓ |

**Account Status Flags:**
- `is_deleted`: Soft delete (False = active account)
- `is_active`: Admin-approved (True = can log in)
- `is_verified`: Email/OTP verified
- `is_staff`: Django admin access

---

## 9. Business Logic Layer

### 9.1 Serializers (accounts/serializers.py)

**Purpose:** Data validation and transformation for API requests

**Key Serializers:**
1. `PatientRegistrationSerializer`
   - Validates patient registration data
   - Creates CustomUser + PatientProfile atomically
   - Normalizes gender input (male → M, female → F)

2. `DoctorRegistrationSerializer`
   - Handles doctor registration with specializations (M2M)
   - Location fields: country, state, city, address, pincode
   - Professional fields: education, experience, license_number

3. `HospitalRegistrationSerializer`
   - Hospital/clinic registration
   - Facility information, emergency services
   - Equipment and services as text fields

### 9.2 Forms (accounts/forms.py)

**Purpose:** Server-side validation for traditional form submissions

**Key Forms:**
- `SubscriptionPlanForm` - Admin subscription plan creation/editing

### 9.3 Signals (accounts/signals.py)

**Purpose:** Automated actions on model changes

**Implemented Signals:**
```python
@receiver(post_save, sender=PatientProfile)
def set_patient_username(sender, instance, created, **kwargs):
    if created:
        instance.user.update_username_from_profile()
```

**Signal Flow:**
```
PatientProfile.objects.create() 
    ↓
Signal: post_save
    ↓
set_patient_username()
    ↓
user.username = patient_profile.full_name
user.save()
```

**All Profile Signals:**
- PatientProfile → set patient username
- DoctorProfile → set doctor username
- HospitalClinicProfile → set hospital username

### 9.4 Context Processors (accounts/context_processors.py)

**Purpose:** Inject data into all template contexts

```python
def user_profile_name(request):
    # Returns {'profile_name': 'Dr. John Doe'} for all templates
```

**Usage in Templates:**
```django
Welcome, {{ profile_name }}
```

### 9.5 Email Utilities (accounts/email_utils.py)

**Purpose:** Email sending abstraction

**Function:**
```python
def send_otp_email(user, otp_code):
    # Sends OTP email using Django EmailMultiAlternatives
    # HTML template: templates/accounts/otp_email.html
```

### 9.6 Probability Calculation Algorithm (symptoms/models.py)

**Purpose:** Calculate illness probability based on selected symptoms

**Algorithm:**
```python
def calculate_illness_probabilities(self, selected_symptoms_data):
    for illness in all_illnesses:
        total_score = 0.0
        matched_symptoms = 0
        
        for selected_symptom in user_symptoms:
            if illness has this symptom:
                # Get weight based on user's severity selection
                weight = illness_symptom.get_severity_weight(user_severity)
                total_score += weight
                matched_symptoms += 1
        
        if matched_symptoms > 0:
            # Normalize by illness symptom count
            base_score = total_score / illness.total_symptoms
            
            # Boost based on match percentage
            match_ratio = matched_symptoms / illness.total_symptoms
            probability = min(0.95, base_score * (1 + match_ratio * 0.5))
            
            if probability >= 0.1:  # Threshold
                results.append({illness, probability, ...})
    
    return top 6 results sorted by probability
```

**Severity Weights:**
- Low severity: 0.3 (default)
- Mid severity: 0.6 (default)
- High severity: 1.0 (default)
- Configurable per illness-symptom relationship

---

## 10. API Endpoints

### 10.1 Accounts App APIs

**Registration:**
- `POST /user/api/register/patient/` - Patient registration
- `POST /user/api/register/doctor/` - Doctor registration
- `POST /user/api/register/hospital/` - Hospital registration

**Validation:**
- `POST /user/api/check-email/` - Check email uniqueness
- `POST /user/api/check-contact-number/` - Check phone uniqueness

**OTP Management:**
- `POST /user/api/verify-otp/` - Verify OTP code
- `POST /user/api/resend-otp/` - Resend OTP
- `POST /user/api/cancel-registration/` - Cancel registration

**Authentication:**
- `POST /user/api/login/` - User login
- `POST /user/api/logout/` - User logout

**Password Reset:**
- `POST /user/api/forgot-password/check/` - Initiate reset
- `POST /user/api/forgot-password/verify-otp/` - Verify reset OTP
- `POST /user/api/forgot-password/reset/` - Set new password
- `POST /user/api/forgot-password/resend-otp/` - Resend reset OTP
- `POST /user/api/forgot-password/cancel/` - Cancel reset

**Doctor Features:**
- `POST /user/api/doctor/toggle-availability/` - Toggle online status
- `GET /user/api/doctor/working-hours/` - Get weekly schedule
- `POST /user/api/doctor/working-hours/save/` - Update schedule

### 10.2 Symptoms App APIs

**Symptom Checker:**
- `GET /api/symptom-check/` - Get body parts
- `POST /api/symptom-check/`
  - `step: 'get_symptoms'` - Get symptoms for body part
  - `step: 'calculate_results'` - Calculate illness probabilities
  - `step: 'ai_results'` - Get AI diagnosis (mock)

**Doctor Discovery:**
- `GET /api/doctors-by-specialist/`
  - Query params: `specialist_id`, `illness_name`, `page`
  - Returns: Doctors with matching specialization

- `GET /api/registered-doctors/`
  - **Action: doctors** (default)
    - Query params: `specialization_id` (required), `country`, `state`, `city`, `page`
    - Returns: Filtered doctors with pagination
  
  - **Action: locations**
    - Query params: `type` (country/state/city), `specialization_id`, `country`, `state`
    - Returns: Unique location values for cascading dropdowns

**API Response Format:**
```json
{
  "doctors": [
    {
      "id": 1,
      "doctor_name": "Dr. John Doe",
      "education": "MBBS, MD",
      "experience": 10,
      "specializations": ["Cardiology", "Internal Medicine"],
      "consultation_fee": "500.00",
      "country": "USA",
      "state": "California",
      "city": "Los Angeles",
      "rating_avg": 4.5,
      "num_reviews": 120,
      "is_available": true,
      "languages_spoken": "English, Spanish",
      "user_email": "doctor@example.com",
      "user_phone": "+1234567890"
    }
  ],
  "total_count": 42,
  "page": 1,
  "total_pages": 3,
  "per_page": 20,
  "status": "success"
}
```

### 10.3 Admin APIs

**Admin Dashboard:**
- `GET /user/admin-dashboard/` - Admin overview
- `GET /user/registered-doctors-list/` - Doctor management
- `GET /user/registered-patients-list/` - Patient management
- `GET /user/registered-hospitals-list/` - Hospital management
- `POST /user/soft-delete-or-recover-account/<pk>/` - Soft delete/restore

**Subscription Management:**
- `GET /user/admin/subscriptions/` - List plans
- `GET /user/admin/subscriptions/create/` - Create plan
- `POST /user/admin/subscriptions/<pk>/edit/` - Edit plan
- `POST /user/admin/subscriptions/<pk>/delete/` - Delete plan

**Contact & Feedback:**
- `GET /user/contact-messages-list/` - View contact messages
- `POST /user/update-message-status/<pk>/` - Update message status
- `POST /user/reply-to-message/<pk>/` - Reply to message
- `GET /user/feedback-list/` - View feedback
- `GET /user/feedback-detail/<pk>/` - Feedback details

---

## 11. Templates & Frontend Architecture

### 11.1 Template Hierarchy

**Base Template:** `templates/base.html`
- Bootstrap 5 layout
- Responsive navbar with role-based menu items
- Footer with contact info
- Common CSS/JS includes
- Block structure: `{% block title %}`, `{% block content %}`, `{% block scripts %}`

**Template Inheritance Pattern:**
```django
{% extends 'base.html' %}
{% load static %}

{% block title %}Page Title{% endblock %}

{% block content %}
<!-- Page content -->
{% endblock %}

{% block scripts %}
<script src="{% static 'js/page-specific.js' %}"></script>
{% endblock %}
```

### 11.2 Frontend JavaScript Architecture

**Pattern:** Object-Oriented JavaScript Classes

**Example: RegisteredDoctorListing Class**
```javascript
class RegisteredDoctorListing {
    constructor(options) {
        this.currentPage = options.currentPage || 1;
        this.filters = {
            specialization_id: '',
            country: '',
            state: '',
            city: ''
        };
    }
    
    init() {
        this.bindFilterEvents();
        this.loadLocationOptions();
        this.searchDoctors();
    }
    
    bindFilterEvents() {
        // Event listeners for filter changes
    }
    
    async searchDoctors() {
        // Fetch API call to load doctors
        const response = await fetch(url);
        this.renderDoctorCards(data);
    }
    
    renderDoctorCards(doctors) {
        // DOM manipulation to display results
    }
}
```

**JavaScript Files Structure:**
- `registered-doctor-listing.js` - Doctor search with location filters
- `recommended-doctor-listing.js` - Post-diagnosis doctor listing
- `doctor-dashboard.js` - Doctor dashboard interactions
- `patient-dashboard.js` - Patient dashboard interactions
- `doctor_registration.js` - Doctor signup form
- `patient_registration.js` - Patient signup form
- `hospital_registration.js` - Hospital signup form
- `login.js` - Login form handling
- `reset-password.js` - Password reset flow

### 11.3 UI/UX Components

**Bootstrap Components Used:**
- Cards (doctor listings, dashboard widgets)
- Modals (doctor details, confirmation dialogs)
- Forms (filters, registration)
- Alerts (validation messages, status notifications)
- Badges (subscription status, account status)
- Pagination (doctor listings)
- Dropdowns (specialization, location filters)

**Custom CSS (static/css/style.css):**
- Custom color scheme
- Doctor card hover effects
- Dashboard card styling
- Disabled state styling
- Responsive adjustments

**Animation Libraries:**
- WOW.js + Animate.css - Scroll animations
- Owl Carousel - Content sliders

### 11.4 Doctor Listing Templates

**Two Listing Templates:**

1. **recommended_doctor_listing.html**
   - Context: From symptom checker results
   - Pre-filtered by specialist_id
   - Shows illness name in header
   - URL: `/recommended-doctors/?specialist_id=X&illness_name=Migraine`

2. **registered_doctors_listing.html**
   - Context: General doctor search
   - Filter UI: Specialization (required) + Country/State/City (optional, cascading)
   - Shows "Select specialization" initial state
   - URL: `/registered-doctors/`

**Common Features:**
- Doctor cards with photo, name, specialization, experience, rating
- "View Details" button → Opens modal with full profile
- "Book Appointment" button → *(To be implemented)*
- Pagination (20 doctors per page)
- Active filters display
- Loading states

---

## 12. Middleware & Signals

### 12.1 Middleware Stack

**From settings.py:**
```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # CORS headers
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

**Middleware Functions:**
1. **SecurityMiddleware** - Security headers
2. **SessionMiddleware** - Session management
3. **CorsMiddleware** - Cross-origin requests (configured for all origins in dev)
4. **CommonMiddleware** - URL normalization, broken link emails
5. **CsrfViewMiddleware** - CSRF protection
6. **AuthenticationMiddleware** - User authentication
7. **MessageMiddleware** - Flash messages
8. **XFrameOptionsMiddleware** - Clickjacking protection

**CORS Configuration:**
```python
CORS_ALLOW_ALL_ORIGINS = True  # Development only
```

### 12.2 Signal Handlers

**Registered Signals:**

1. **Profile Username Sync**
   ```python
   @receiver(post_save, sender=PatientProfile)
   def set_patient_username(sender, instance, created, **kwargs):
       if created:
           instance.user.update_username_from_profile()
   ```
   - Triggers: On PatientProfile, DoctorProfile, HospitalClinicProfile creation
   - Action: Updates CustomUser.username with profile name

**Signal Flow Diagram:**
```
User Registration
    ↓
CustomUser.objects.create_user()
    ↓
PatientProfile.objects.create(user=user)
    ↓
post_save signal fired
    ↓
set_patient_username() receiver
    ↓
user.update_username_from_profile()
    ↓
user.username = patient_profile.full_name
user.save()
```

---

## 13. Database Design & Schema

### 13.1 Database Configuration

**Database:** PostgreSQL
**Connection Settings:**
```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DATABASE_NAME"),
        "USER": env("DATABASE_USER"),
        "PASSWORD": env("DATABASE_PASSWORD"),
        "HOST": env("DATABASE_HOST"),
        "PORT": env("DATABASE_PORT"),
    }
}
```

**Timezone:** `Asia/Kolkata`
**Time Zone Aware:** `USE_TZ = True`

### 13.2 Database Indexes

**Optimized Indexes:**

1. **DoctorProfile:**
   ```python
   class Meta:
       indexes = [
           models.Index(fields=['is_available', 'experience']),
           models.Index(fields=['rating_avg', 'num_reviews']),
       ]
   ```
   - Purpose: Fast filtering/sorting for doctor listings

2. **DoctorWorkingHours:**
   ```python
   class Meta:
       unique_together = ('doctor', 'day_of_week')
       ordering = ['day_of_week']
   ```
   - Purpose: Ensure one record per day, ordered retrieval

3. **IllnessSymptom:**
   ```python
   class Meta:
       unique_together = ('illness', 'symptom')
   ```
   - Purpose: No duplicate symptom relationships

4. **SymptomCheckResult:**
   ```python
   class Meta:
       unique_together = ('session', 'illness')
       ordering = ['-probability_score']
   ```
   - Purpose: Ordered results, no duplicates

### 13.3 Data Integrity Constraints

**Foreign Key Cascades:**
- User deletion → CASCADE on profiles (hard delete)
- Profile deletion → CASCADE on related data
- Soft delete via `is_deleted` flag for users

**Unique Constraints:**
- CustomUser: email, phone_number
- DoctorProfile: license_number
- Specialization: name
- Illness: name
- BodyPart: name

**Validators:**
- Experience: MinValueValidator(0)
- Age: MinValueValidator(1), MaxValueValidator(120)
- Probability scores: MinValueValidator(0.0), MaxValueValidator(1.0)
- Severity weights: MinValueValidator(0.0), MaxValueValidator(1.0)
- File uploads: validate_icon_file (size, format)

### 13.4 Database Schema Diagram

```sql
-- Core User & Authentication
CustomUser
├── id (PK)
├── email (UNIQUE)
├── phone_number (UNIQUE)
├── password (hashed)
├── user_type (patient/doctor/hospital/admin/staff)
├── is_verified (BOOLEAN)
├── is_active (BOOLEAN)
├── is_deleted (BOOLEAN)
└── date_joined

OTP
├── id (PK)
├── user_id (FK → CustomUser)
├── code (6 digits)
├── otp_type (email/phone)
├── created_at
├── expires_at
└── is_used

-- Profiles
PatientProfile
├── id (PK)
├── user_id (FK → CustomUser, UNIQUE)
├── full_name
├── date_of_birth
├── gender
├── address
├── emergency_contact
└── blood_group

DoctorProfile
├── id (PK)
├── user_id (FK → CustomUser, UNIQUE)
├── doctor_name
├── education
├── experience
├── license_number (UNIQUE)
├── consultation_fee
├── country, state, city, address, pincode
├── rating_avg (indexed)
├── num_reviews (indexed)
└── is_available

Specialization
├── id (PK)
├── name (UNIQUE)
└── description

DoctorProfile_specializations (M2M)
├── doctorprofile_id (FK)
└── specialization_id (FK)

HospitalClinicProfile
├── id (PK)
├── user_id (FK → CustomUser, UNIQUE)
├── name
├── registration_number
├── country, state, city
├── emergency_services
└── facilities

HospitalDoctors
├── id (PK)
├── hospital_id (FK → HospitalClinicProfile)
├── doctor_id (FK → DoctorProfile)
├── joining_date
└── is_active
UNIQUE(hospital, doctor)

DoctorWorkingHours
├── id (PK)
├── doctor_id (FK → DoctorProfile)
├── day_of_week (0-6)
├── start_time
├── end_time
└── is_off
UNIQUE(doctor, day_of_week)

-- Symptom Checker
BodyPart
├── id (PK)
├── name (UNIQUE)
└── icon (FileField)

Symptom
├── id (PK)
├── name
└── description

Symptom_body_parts (M2M)
├── symptom_id (FK)
└── bodypart_id (FK)

Illness
├── id (PK)
├── name (UNIQUE)
├── severity
└── treatment_advice

Illness_specializations (M2M)
├── illness_id (FK)
└── specialization_id (FK)

IllnessSymptom
├── id (PK)
├── illness_id (FK → Illness)
├── symptom_id (FK → Symptom)
├── low_severity_weight (0.3)
├── mid_severity_weight (0.6)
└── high_severity_weight (1.0)
UNIQUE(illness, symptom)

SymptomCheckSession
├── id (UUID, PK)
├── patient_id (FK → PatientProfile, nullable)
├── created_at
└── completed_at

SelectedSymptom
├── id (PK)
├── session_id (FK → SymptomCheckSession)
├── symptom_id (FK → Symptom)
└── user_severity (low/mid/high)
UNIQUE(session, symptom)

SymptomCheckResult
├── id (PK)
├── session_id (FK → SymptomCheckSession)
├── illness_id (FK → Illness)
└── probability_score
UNIQUE(session, illness)

-- Subscriptions
SubscriptionPlan
├── id (PK)
├── name
├── user_type
├── monthly_price
├── half_yearly_discount
├── yearly_discount
├── receiver_qr
└── is_active

UserSubscription
├── id (PK)
├── user_id (FK → CustomUser)
├── subscription_plan_id (FK → SubscriptionPlan)
├── start_date
├── end_date
├── duration_in_months
└── final_amount_paid

-- Contact & Feedback
ContactMessage
├── id (PK)
├── user_id (FK → CustomUser, nullable)
├── name, email, phone
├── subject, message
├── status (pending/read/replied)
└── is_deleted

Feedback
├── id (PK)
├── user_id (FK → CustomUser, nullable)
├── role (patient/doctor/hospital/other)
├── symptoms_understanding
├── illness_suggestion
├── rate_us (1-5)
└── improvement_suggestion
```

---

## 14. External Integrations

### 14.1 Email System

**Email Backend:** Django's default (SMTP)
**Configuration:** Via environment variables
**Use Cases:**
- OTP delivery for registration
- OTP delivery for password reset
- Admin replies to contact messages

**Email Utils:**
```python
# accounts/email_utils.py
def send_otp_email(user, otp_code):
    subject = 'Your OTP Code'
    html_content = render_to_string('accounts/otp_email.html', {
        'user': user,
        'otp_code': otp_code
    })
    email = EmailMultiAlternatives(subject, '', to=[user.email])
    email.attach_alternative(html_content, "text/html")
    email.send()
```

### 14.2 CKEditor Integration

**Purpose:** Rich text editing for blog posts
**Package:** `django-ckeditor-5`
**Configuration:** Included in INSTALLED_APPS
**URL:** `/ckeditor5/` - CKEditor static files

### 14.3 AI Diagnosis (Mock Integration)

**Current Status:** Mock implementation
**Placeholder for:** OpenAI API, Google Health API, or custom ML model
**Location:** `symptoms/views.py → SymptomCheckAPIView.get_ai_diagnosis()`

**Mock Logic:**
```python
def get_ai_diagnosis(self, symptoms_list):
    # Rule-based mock responses
    if any('cough' in symptom.lower() for symptom in symptoms_list):
        return [{
            'illness': {'name': 'Common Cold', ...},
            'probability_percentage': 75,
            'confidence': 'high'
        }]
```

**Future Integration Point:**
```python
# Replace with actual API call
import openai
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[{
        "role": "system",
        "content": "You are a medical diagnosis assistant."
    }, {
        "role": "user",
        "content": f"Analyze these symptoms: {symptoms_list}"
    }]
)
```

### 14.4 Payment Gateway (Potential)

**Current Status:** Not implemented
**Evidence:** Subscription plans have QR code fields (`receiver_qr`)
**Use Case:** Subscription payment processing
**Potential Integration:** Razorpay, Stripe, PayPal

---

## 15. Security Practices

### 15.1 Authentication Security

✅ **Implemented:**
- Password hashing with Django's PBKDF2
- Email-based OTP verification
- OTP expiration (5 minutes default)
- One-time OTP usage (`is_used` flag)
- Session-based authentication
- CSRF protection enabled

⚠️ **Considerations:**
- No rate limiting on OTP generation (potential abuse)
- No account lockout after failed login attempts
- No 2FA beyond OTP for registration

### 15.2 Authorization Security

✅ **Implemented:**
- Role-based access control via `user_type`
- Account activation via `is_active` flag
- Email verification via `is_verified` flag
- Soft delete via `is_deleted` flag
- Admin verification required for doctors/hospitals
- Session data validation

⚠️ **Gaps:**
- Some views lack explicit permission checks
- No object-level permissions (Django Guardian not used)

### 15.3 Data Protection

✅ **Implemented:**
- Database credentials in environment variables
- SECRET_KEY in environment variable
- Password fields marked as `write_only` in serializers
- File upload validation (size, format)
- SQL injection protection via Django ORM
- XSS protection via template auto-escaping

⚠️ **Missing:**
- No encryption at rest for sensitive data (license numbers, etc.)
- No PII (Personally Identifiable Information) masking in logs

### 15.4 CSRF Protection

✅ **Configuration:**
```python
MIDDLEWARE = [
    ...
    'django.middleware.csrf.CsrfViewMiddleware',
    ...
]
```

⚠️ **Issue:**
```python
@method_decorator(csrf_exempt, name='dispatch')
class SymptomCheckAPIView(View):
    ...
```
- CSRF exempted for symptom checker API
- Should use CSRF tokens or alternative authentication for APIs

### 15.5 CORS Configuration

⚠️ **Development Setting:**
```python
CORS_ALLOW_ALL_ORIGINS = True  # Should be restricted in production
```

**Recommendation:**
```python
# Production
CORS_ALLOWED_ORIGINS = [
    "https://yourdomain.com",
]
```

### 15.6 File Upload Security

✅ **Implemented:**
```python
def validate_icon_file(value):
    valid_extensions = ['.png', '.svg', '.jpg', '.jpeg']
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in valid_extensions:
        raise ValidationError('Unsupported file format.')
    if value.size > 2 * 1024 * 1024:  # 2MB limit
        raise ValidationError('File size must be less than 2MB.')
```

### 15.7 Security Headers

✅ **Enabled:**
- SecurityMiddleware (HTTPS redirect, HSTS, etc. in production)
- XFrameOptionsMiddleware (Clickjacking protection)

⚠️ **Missing:**
- Content Security Policy (CSP) headers
- Referrer-Policy headers

---

## 16. Performance Considerations

### 16.1 Database Optimizations

✅ **Implemented:**
- Composite indexes on `DoctorProfile` (is_available + experience, rating + reviews)
- `.select_related()` for foreign key queries
- `.prefetch_related()` for M2M relationships
- Cached aggregates (rating_avg, num_reviews)

**Example:**
```python
doctors = DoctorProfile.objects.filter(
    specializations=specialization,
    user__is_verified=True
).select_related('user').order_by('-rating_avg', '-num_reviews')
```

⚠️ **Missing:**
- No database query logging/monitoring
- No N+1 query detection in development

### 16.2 Pagination

✅ **Implemented:**
- 20 items per page for doctor listings
- Page-based pagination
- Total count returned for UI

**Example:**
```python
per_page = 20
start_idx = (page - 1) * per_page
end_idx = start_idx + per_page
paginated_doctors = doctors[start_idx:end_idx]
```

### 16.3 Caching

⚠️ **Not Implemented:**
- No Django cache framework configured
- No Redis/Memcached integration
- No template fragment caching
- No view-level caching

**Recommendation:**
```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

### 16.4 Static Files

✅ **Configuration:**
```python
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
```

⚠️ **Production Considerations:**
- Should use CDN for static files
- Should enable gzip compression
- Should use WhiteNoise or similar for static file serving

### 16.5 API Response Optimization

✅ **Good Practices:**
- Minimal data serialization (only necessary fields)
- JSON responses for AJAX
- Pagination to limit response size

⚠️ **Missing:**
- No API response compression
- No ETag support for caching
- No GraphQL for selective field retrieval

### 16.6 Frontend Performance

✅ **Implemented:**
- Minified Bootstrap CSS
- Minified third-party JS libraries
- Lazy loading with WOW.js

⚠️ **Missing:**
- No image optimization/lazy loading
- No code splitting for JavaScript
- No service workers for offline support

---

## 17. Code Quality Assessment

### 17.1 Code Organization

✅ **Strengths:**
- Clear separation of concerns (models, views, serializers)
- Modular app structure
- Consistent naming conventions
- Feature-specific JavaScript classes

⚠️ **Areas for Improvement:**
- Some view functions are very long (1665 lines in accounts/views.py)
- Business logic mixed with view logic
- Could benefit from service layer pattern

### 17.2 Testing

⚠️ **Status:**
- `tests.py` files exist in all apps
- No test code found during analysis
- No test coverage configured

**Recommendation:**
```python
# accounts/tests.py
from django.test import TestCase
from .models import CustomUser, PatientProfile

class PatientRegistrationTest(TestCase):
    def test_patient_creation(self):
        user = CustomUser.objects.create_user(
            email='test@example.com',
            password='password123',
            user_type='patient'
        )
        self.assertEqual(user.user_type, 'patient')
```

### 17.3 Documentation

✅ **Present:**
- Docstrings in some functions
- Inline comments for complex logic
- Help text on model fields

⚠️ **Missing:**
- No API documentation (Swagger/OpenAPI)
- No inline type hints
- No developer setup guide

### 17.4 Error Handling

✅ **Implemented:**
- Try-except blocks in API views
- Validation errors via serializers
- HTTP status codes returned correctly

⚠️ **Inconsistent:**
```python
try:
    specialization = Specialization.objects.get(id=specialist_id)
except Specialization.DoesNotExist:
    return JsonResponse({'error': 'Invalid specialist'}, status=400)
except Exception as e:
    logger.error(f"Error: {str(e)}")
    return JsonResponse({'error': str(e)}, status=500)
```
- Some views have comprehensive error handling
- Others have minimal or no error handling

### 17.5 Logging

✅ **Configured:**
```python
import logging
logger = logging.getLogger("accounts")
logger.info(f"User registered: {user.email}")
logger.error(f"Error fetching doctors: {str(e)}")
```

⚠️ **Missing:**
- No centralized logging configuration in settings.py
- No log rotation configuration
- No structured logging (JSON format)

### 17.6 Code Duplication

⚠️ **Observed:**
- Similar doctor filtering logic in multiple views
- Repeated subscription status checking
- Duplicated serialization patterns

**Recommendation:** Extract to utility functions or services

### 17.7 Django Best Practices

✅ **Followed:**
- Custom user model defined early
- Migrations tracked in version control
- Settings use environment variables
- Apps registered in INSTALLED_APPS

⚠️ **Violations:**
- CSRF exemption on some API views
- CORS allow all origins (dev setting)
- Some hardcoded values (per_page = 20)

---

## 18. Existing Features Analysis

### 18.1 Doctor Discovery System

**Two Discovery Flows:**

#### Flow 1: Symptom-Based Recommendation
```
Patient → Symptom Checker
    ↓
Selects body parts & symptoms
    ↓
System calculates illness probabilities
    ↓
Results page shows matched illnesses + specialist recommendations
    ↓
Patient clicks "Find & Book Appointment"
    ↓
Redirect: /recommended-doctors/?specialist_id=5&illness_name=Migraine
    ↓
RecommendedDoctorListingView
    ↓
API: /api/doctors-by-specialist/?specialist_id=5
    ↓
Returns doctors with specialization, ordered by rating
    ↓
Doctor cards displayed with:
- "View Details" (modal)
- "Book Appointment" (not yet implemented)
```

#### Flow 2: Manual Doctor Search
```
Patient → Find Doctors page
    ↓
/registered-doctors/
    ↓
RegisteredDoctorsListingView
    ↓
Filter UI: Specialization (required), Country/State/City (optional, cascading)
    ↓
User selects Specialization
    ↓
API: /api/registered-doctors/?action=locations&type=country&specialization_id=5
    ↓
Country dropdown populated
    ↓
User selects Country → State dropdown enabled
    ↓
API: /api/registered-doctors/?action=locations&type=state&specialization_id=5&country=USA
    ↓
State dropdown populated
    ↓
User selects State → City dropdown enabled
    ↓
API: /api/registered-doctors/?action=locations&type=city&specialization_id=5&country=USA&state=CA
    ↓
City dropdown populated
    ↓
User clicks "Search Doctors"
    ↓
API: /api/registered-doctors/?specialization_id=5&country=USA&state=CA&city=Los Angeles
    ↓
RegisteredDoctorsAPIView.get_doctors()
    ↓
DoctorProfile.objects.filter(specializations=5, country__icontains='USA', ...)
    ↓
Doctor cards displayed with:
- "View Details" (modal)
- "Book Appointment" (not yet implemented)
```

**Common Doctor Card Components:**
- Doctor photo (placeholder if not uploaded)
- Name, education, experience
- Specializations (list)
- Consultation fee
- Location (city, state, country)
- Rating (stars) + review count
- Availability status (online/offline)
- Languages spoken
- Contact: email, phone

**Modal: Doctor Details**
- Full profile information
- Working hours
- Awards/certifications
- Bio
- "Book Appointment" button (not yet connected)

### 18.2 Doctor Types & Availability

**Two Doctor Types:**

1. **Independent Doctors**
   - Standalone DoctorProfile
   - Can manage own working hours
   - Can toggle availability

2. **Hospital-Associated Doctors**
   - DoctorProfile linked via HospitalDoctors
   - Associated with HospitalClinicProfile
   - Same availability management

**Working Hours System:**
- 7 records per doctor (Monday-Sunday)
- Each day: start_time, end_time, is_off
- Managed via doctor dashboard
- Stored in DoctorWorkingHours model

**Example:**
```
Monday: 9:00 AM - 5:00 PM
Tuesday: 9:00 AM - 5:00 PM
Wednesday: OFF
Thursday: 9:00 AM - 5:00 PM
Friday: 9:00 AM - 5:00 PM
Saturday: 10:00 AM - 2:00 PM
Sunday: OFF
```

### 18.3 Subscription System

**Features:**
- Admin creates subscription plans
- Plans target specific user types (patient/doctor/hospital)
- Pricing: monthly, half-yearly, yearly discounts
- QR code upload for payment
- Date-based subscription periods
- Computed `is_active` property (not DB field)

**Dashboard Integration:**
- Shows subscription status (Active/Expired)
- Displays start/end dates
- Warning when expiring soon (< 7 days)
- Alert when expired
- Call-to-action to renew

**Logic:**
```python
def has_active_subscription(user):
    today = timezone.now().date()
    return user.subscriptions.filter(
        start_date__lte=today,
        end_date__gte=today
    ).exists()
```

### 18.4 Dashboards

**Patient Dashboard:**
- Welcome message with name
- Account status badges (Active/Inactive, Verified/Pending)
- Subscription card
- Quick actions (yet to be implemented)

**Doctor Dashboard:**
- Welcome message with doctor name
- Account status badges
- Verification warning if pending
- Subscription card
- Availability toggle
- Working hours management
- Appointment notifications (placeholder)

**Admin Dashboard:**
- User management (patients, doctors, hospitals)
- Soft delete/restore accounts
- Subscription plan CRUD
- Contact message management
- Feedback review

### 18.5 Contact & Feedback System

**Contact Us:**
- Anonymous or authenticated users
- Fields: name, email, phone, subject, message
- Status: pending → read → replied
- Admin can reply via email

**Feedback:**
- Role-specific (patient/doctor/hospital/other)
- Medical feedback: symptom understanding, illness accuracy, doctor suggestions
- Feature request: appointment booking
- Overall rating (1-5 stars)
- Improvement suggestions

---

## 19. Appointment Booking System Requirements

### 19.1 Feature Overview

**Objective:** Implement comprehensive appointment booking system connecting patients with doctors

**Integration Points:**
- "Book Appointment" button in recommended_doctor_listing.html
- "Book Appointment" button in registered_doctors_listing.html
- Both buttons should trigger same booking flow

### 19.2 Core Requirements

#### Patient Side - Book Appointment

**Functional Requirements:**
1. **Doctor Selection**
   - Pre-selected from doctor card
   - Display doctor name, specialization, fee

2. **Date Selection**
   - Date picker for appointment date
   - Validation: Must be >= today
   - Optional: Max 60 days in future

3. **Description/Message**
   - Text area for patient to describe issue
   - Optional but recommended field

4. **Submission**
   - Create appointment with status = PENDING
   - Assign to selected doctor
   - Show success message

5. **Cancellation**
   - Patient can cancel if status = PENDING
   - Must provide cancellation reason
   - Status changes to CANCELED

#### Doctor Side - Manage Appointments

**Functional Requirements:**
1. **View Requests**
   - Dashboard notification for PENDING appointments
   - List view with patient details:
     - Patient name, phone, address
     - Requested date
     - Description
     - Booking timestamp

2. **Accept Appointment**
   - Must provide approximate visit time (TimeField)
   - Status → ACCEPTED
   - Store `doctor_provided_time`
   - Remove from notification list

3. **Reject Appointment**
   - Must provide rejection reason (Required)
   - Status → REJECTED
   - Remove from notification list

4. **Confirmation**
   - Require confirmation dialog for both actions

### 19.3 Business Rules

**Date Validations:**
- Appointment date >= today (no past dates)
- Optional: Appointment date <= today + 60 days

**Role Validation:**
- Only patients can create appointments
- Only doctors can accept/reject appointments
- Both independent and hospital-associated doctors can manage

**Duplicate Booking Rule (Optional):**
- Prevent same patient booking same doctor on same date with PENDING status

**State Transitions:**
```
PENDING → ACCEPTED (by doctor)
PENDING → REJECTED (by doctor)
PENDING → CANCELED (by patient)
ACCEPTED → [locked]
REJECTED → [locked]
CANCELED → [locked]
```

**Notification Logic:**
- Doctor dashboard shows count of PENDING appointments
- Each PENDING appointment appears as notification
- On Accept/Reject: notification removed immediately

### 19.4 Data Model Requirements

**Appointment Model:**
```python
class Appointment(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('CANCELED', 'Canceled'),
    )
    
    # Relationships
    patient = ForeignKey(PatientProfile, on_delete=CASCADE)
    doctor = ForeignKey(DoctorProfile, on_delete=CASCADE)
    
    # Appointment details
    appointment_date = DateField()
    patient_message = TextField(blank=True)
    
    # Status
    status = CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    
    # Doctor response
    doctor_provided_time = TimeField(null=True, blank=True)
    rejection_reason = TextField(blank=True)
    
    # Cancellation
    cancellation_reason = TextField(blank=True)
    
    # Timestamps
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
```

### 19.5 API Endpoints Required

**Patient APIs:**
- `POST /api/appointments/create/` - Create appointment
- `GET /api/appointments/my-appointments/` - List patient's appointments
- `POST /api/appointments/<id>/cancel/` - Cancel appointment

**Doctor APIs:**
- `GET /api/appointments/pending/` - Get PENDING appointments
- `GET /api/appointments/all/` - Get all appointments (with filters)
- `POST /api/appointments/<id>/accept/` - Accept with time
- `POST /api/appointments/<id>/reject/` - Reject with reason

### 19.6 UI/UX Requirements

**Book Appointment Modal:**
```
┌─────────────────────────────────────┐
│ Book Appointment with Dr. John Doe  │
├─────────────────────────────────────┤
│ Specialization: Cardiology          │
│ Consultation Fee: $500              │
│                                     │
│ Select Date: [Date Picker ▼]       │
│                                     │
│ Describe Your Issue:                │
│ [Text Area........................] │
│ [.................................]  │
│                                     │
│ [Cancel]  [Book Appointment]        │
└─────────────────────────────────────┘
```

**Doctor Dashboard Notifications:**
```
┌─────────────────────────────────────┐
│ Pending Appointments (3)            │
├─────────────────────────────────────┤
│ ┌─────────────────────────────────┐ │
│ │ Patient: John Smith             │ │
│ │ Date: Feb 25, 2026              │ │
│ │ Issue: Chest pain since...      │ │
│ │ Booked: Feb 21, 2026 10:30 AM   │ │
│ │                                 │ │
│ │ [Accept]  [Reject]              │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

**Accept Appointment Dialog:**
```
┌─────────────────────────────────────┐
│ Accept Appointment                  │
├─────────────────────────────────────┤
│ Patient: John Smith                 │
│ Date: Feb 25, 2026                  │
│                                     │
│ Appointment Time: [__:__ AM/PM ▼]  │
│                                     │
│ [Cancel]  [Confirm Accept]          │
└─────────────────────────────────────┘
```

**Reject Appointment Dialog:**
```
┌─────────────────────────────────────┐
│ Reject Appointment                  │
├─────────────────────────────────────┤
│ Patient: John Smith                 │
│ Date: Feb 25, 2026                  │
│                                     │
│ Rejection Reason: *                 │
│ [Text Area........................] │
│                                     │
│ [Cancel]  [Confirm Reject]          │
└─────────────────────────────────────┘
```

### 19.7 Optional Enhancements

1. **Email Notifications**
   - Send email to doctor on new appointment
   - Send email to patient on accept/reject

2. **SMS Notifications**
   - SMS reminders 24 hours before appointment

3. **Auto-Expire**
   - Auto-reject PENDING appointments after X days

4. **Appointment History**
   - Patient view: All past appointments
   - Doctor view: All past appointments

5. **Rescheduling**
   - Allow accepted appointments to be rescheduled

6. **Rating System**
   - Allow patient to rate doctor after appointment (if ACCEPTED and date passed)

### 19.8 Technical Constraints

**DO NOT:**
- Modify existing functionality
- Change existing design/UI
- Change global CSS/JS properties
- Remove or alter current features

**DO:**
- Reuse existing frontend dependencies (Bootstrap, Font Awesome, etc.)
- Follow existing code patterns and conventions
- Use existing JavaScript class structure
- Maintain consistent UI/UX with rest of application
- Use Django ORM for all database operations
- Use DRF for API endpoints
- Include proper validation and error handling

---

## Conclusion

This architecture document provides a comprehensive analysis of the COZOM Healthcare Django project. The application demonstrates:

**Strengths:**
- Well-structured modular architecture
- Clear separation of concerns
- Modern REST API design
- Comprehensive feature set
- Good use of Django best practices

**Areas for Improvement:**
- Test coverage
- Performance optimizations (caching)
- Security hardening (CSRF on APIs, CORS restrictions)
- Code documentation
- Error handling consistency

**Ready for New Features:**
The codebase is well-organized and ready for the implementation of the Appointment Booking System. The existing patterns and structures provide clear guidance for new feature development.

---

**Document Version:** 1.0  
**Last Updated:** February 21, 2026  
**Next Steps:** Implement Appointment Booking System as per requirements in Section 19
