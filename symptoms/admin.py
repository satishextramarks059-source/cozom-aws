from django.contrib import admin
from django.db import models
from .models import (
    BodyPart,
    Symptom,
    Illness,
    IllnessSymptom,
    SymptomCheckSession,
    SelectedSymptom,
    SymptomCheckResult
)

# --- Inline Admin Classes for Relationships ---

class IllnessSymptomInline(admin.TabularInline):
    """Inline for managing Symptoms within an Illness."""
    model = IllnessSymptom
    extra = 1 # Number of extra forms to display

class SelectedSymptomInline(admin.TabularInline):
    """Inline for viewing/managing SelectedSymptoms within a SymptomCheckSession."""
    model = SelectedSymptom
    extra = 0 # Don't show extra empty forms
    readonly_fields = ('symptom', 'user_severity')
    can_delete = False

class SymptomCheckResultInline(admin.TabularInline):
    """Inline for viewing SymptomCheckResults within a SymptomCheckSession."""
    model = SymptomCheckResult
    extra = 0
    readonly_fields = ('illness', 'probability_score', 'reasoning')
    can_delete = False


# --- ModelAdmin Classes ---

@admin.register(BodyPart)
class BodyPartAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'description')
    search_fields = ('name',)

@admin.register(Symptom)
class SymptomAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name', 'description')
    # Use filter_horizontal for the ManyToManyField for better UX
    filter_horizontal = ('body_parts',) 

@admin.register(Illness)
class IllnessAdmin(admin.ModelAdmin):
    list_display = ('name', 'severity', 'created_at', 'updated_at')
    list_filter = ('severity', 'specializations')
    search_fields = ('name', 'description')
    date_hierarchy = 'created_at'
    # Inlines for managing symptoms related to this illness
    inlines = [IllnessSymptomInline]
    # Use filter_horizontal for the ManyToManyField
    filter_horizontal = ('specializations',)

@admin.register(IllnessSymptom)
class IllnessSymptomAdmin(admin.ModelAdmin):
    list_display = ('illness', 'symptom', 'low_severity_weight', 'mid_severity_weight', 'high_severity_weight')
    list_filter = ('illness', 'symptom')
    search_fields = ('illness__name', 'symptom__name')

@admin.register(SymptomCheckSession)
class SymptomCheckSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'created_at', 'completed_at')
    list_filter = ('created_at', 'completed_at', 'patient')
    readonly_fields = ('id', 'created_at')
    inlines = [SelectedSymptomInline, SymptomCheckResultInline] # Show related data within the session

@admin.register(SelectedSymptom)
class SelectedSymptomAdmin(admin.ModelAdmin):
    list_display = ('session', 'symptom', 'user_severity')
    list_filter = ('user_severity', 'symptom')
    search_fields = ('session__id', 'symptom__name')

@admin.register(SymptomCheckResult)
class SymptomCheckResultAdmin(admin.ModelAdmin):
    list_display = ('session', 'illness', 'probability_score')
    list_filter = ('illness',)
    ordering = ('-probability_score',)
    search_fields = ('session__id', 'illness__name')