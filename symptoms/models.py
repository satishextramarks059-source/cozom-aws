import uuid
import os
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone
from accounts.models import Specialization, PatientProfile

# Validate icon file type and size
def validate_icon_file(value):
    valid_extensions = ['.png', '.svg', '.jpg', '.jpeg']
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in valid_extensions:
        raise ValidationError('Unsupported file format. Please upload PNG, SVG, JPG, or JPEG files.')
    
    # Check file size (max 2MB)
    if value.size > 2 * 1024 * 1024:
        raise ValidationError('File size must be less than 2MB.')

class BodyPart(models.Model):
    name = models.CharField(max_length=100, unique=True)
    icon = models.FileField(
        upload_to="body_parts/icons/", 
        blank=True, 
        null=True,
        validators=[validate_icon_file]
    )
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name
    
    def clean(self):
        if self.icon:
            validate_icon_file(self.icon)

class Symptom(models.Model):
    SEVERITY_LEVELS = (
        ('low', 'Low'),
        ('mid', 'Medium'),
        ('high', 'High'),
    )
    
    name = models.CharField(max_length=200)
    body_parts = models.ManyToManyField(BodyPart, related_name='symptoms', blank=True)
    description = models.TextField(blank=True)
    common_causes = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

class Illness(models.Model):
    SEVERITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    )
    
    # Prevalence weight: higher = more common, lower = rarer
    # Default 0.5 (moderate). Common diseases = 1.0, rare = 0.2–0.3
    prevalence_weight = models.FloatField(
        default=0.5,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Weight based on how common this illness is (1.0 = very common, 0.2 = very rare)"
    )
    
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    specializations = models.ManyToManyField(Specialization, related_name='illnesses', blank=True)
    common_causes = models.TextField(blank=True)
    prevention_tips = models.TextField(blank=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='low')
    treatment_advice = models.TextField(blank=True)
    when_to_see_doctor = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class IllnessSymptom(models.Model):
    illness = models.ForeignKey(Illness, on_delete=models.CASCADE, related_name='illness_symptoms')
    symptom = models.ForeignKey(Symptom, on_delete=models.CASCADE)
    
    # Severity impact factors (how much each user-selected severity affects probability)
    low_severity_weight = models.FloatField(default=0.3, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    mid_severity_weight = models.FloatField(default=0.6, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    high_severity_weight = models.FloatField(default=1.0, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])

    class Meta:
        unique_together = ('illness', 'symptom')

class SymptomCheckSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Symptom Check Session {self.id}"

class SelectedSymptom(models.Model):
    SEVERITY_CHOICES = (
        ('low', 'Low'),
        ('mid', 'Medium'),
        ('high', 'High'),
    )
    
    session = models.ForeignKey(SymptomCheckSession, on_delete=models.CASCADE, related_name='selected_symptoms')
    symptom = models.ForeignKey(Symptom, on_delete=models.CASCADE)
    user_severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    
    class Meta:
        unique_together = ('session', 'symptom')

    def __str__(self):
        return f"{self.symptom.name} ({self.user_severity}) in session {self.session.id}"

class SymptomCheckResult(models.Model):
    session = models.ForeignKey(SymptomCheckSession, on_delete=models.CASCADE, related_name='results')
    illness = models.ForeignKey(Illness, on_delete=models.CASCADE)
    probability_score = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    reasoning = models.TextField(blank=True)
    
    class Meta:
        unique_together = ('session', 'illness')
        ordering = ['-probability_score']

    def __str__(self):
        return f"{self.illness.name}: {self.probability_score:.2f}"


# ------------------- Doctor‑Thinking Probability Calculation -------------------
def calculate_illness_probabilities(self, selected_symptoms_data):
    """
    Calculate illness probabilities based on:
        - matched symptoms (match ratio)
        - user‑selected severity weights (from IllnessSymptom)
        - prevalence weight (common vs rare)
    
    Returns list of dicts with:
        - illness
        - final_score (0–1, higher = more likely)
        - matched_symptoms_count
        - total_illness_symptoms
    """
    illnesses = Illness.objects.prefetch_related('illness_symptoms').all()
    results = []
    
    for illness in illnesses:
        total_severity_weight = 0.0
        matched_symptoms_count = 0
        illness_symptom_count = illness.illness_symptoms.count()
        
        if illness_symptom_count == 0:
            continue
        
        # For each selected symptom, check if it belongs to this illness
        for symptom_data in selected_symptoms_data:
            symptom_id = symptom_data['symptom_id']
            user_severity = symptom_data['severity']
            
            try:
                illness_symptom = illness.illness_symptoms.get(symptom_id=symptom_id)
                
                # Get severity weight based on user's choice
                if user_severity == 'low':
                    weight = illness_symptom.low_severity_weight
                elif user_severity == 'mid':
                    weight = illness_symptom.mid_severity_weight
                else:  # high
                    weight = illness_symptom.high_severity_weight
                
                total_severity_weight += weight
                matched_symptoms_count += 1
                
            except IllnessSymptom.DoesNotExist:
                # Symptom not associated – ignore
                continue
        
        if matched_symptoms_count == 0:
            continue
        
        # 1. Match ratio: how many of this illness's symptoms are present
        match_ratio = matched_symptoms_count / illness_symptom_count
        
        # 2. Average severity weight of matched symptoms (normalized to 0–1 range)
        avg_severity = total_severity_weight / matched_symptoms_count
        
        # 3. Prevalence weight (doctor‑thinking: common diseases first)
        prevalence = illness.prevalence_weight
        
        # 4. Final score = match_ratio × avg_severity × prevalence
        #    (capped at 1.0)
        final_score = match_ratio * avg_severity * prevalence
        final_score = min(final_score, 1.0)
        
        # Only include if score >= 0.05 (very low matches ignored)
        if final_score >= 0.05:
            results.append({
                'illness': illness,
                'final_score': final_score,
                'matched_symptoms_count': matched_symptoms_count,
                'total_illness_symptoms': illness_symptom_count
            })
    
    # Sort by final_score descending (common + high severity matches on top)
    results.sort(key=lambda x: x['final_score'], reverse=True)
    return results[:10]   # Return top 10 for frontend


# Attach the method to SymptomCheckSession
SymptomCheckSession.calculate_illness_probabilities = calculate_illness_probabilities