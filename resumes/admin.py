from django.contrib import admin
from .models import ParsedResume, ProfileCompletion
from .models import Job, JobApplication, SavedJob

@admin.register(ParsedResume)
class ParsedResumeAdmin(admin.ModelAdmin):
    list_display = ['user', 'original_filename', 'status', 'skill_count', 'experience_years', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'original_filename']
    readonly_fields = ['created_at', 'updated_at', 'parsed_data']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'original_filename', 'file')
        }),
        ('Processing Status', {
            'fields': ('status', 'error_message')
        }),
        ('Parsed Data', {
            'fields': ('parsed_data', 'skills', 'experience_years', 'education_level'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def skill_count(self, obj):
        return obj.skill_count
    skill_count.short_description = 'Skills'


@admin.register(ProfileCompletion)
class ProfileCompletionAdmin(admin.ModelAdmin):
    list_display = ['user', 'completion_score', 'last_calculated']
    list_filter = ['completion_score', 'last_calculated']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['last_calculated']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Completion Details', {
            'fields': ('completion_score', 'missing_fields', 'suggestions')
        }),
        ('Timestamp', {
            'fields': ('last_calculated',)
        }),
    )

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "company",
        "job_type",
        "work_mode",
        "experience_level",
        "status",
        "location",
        "created_at",
    )
    list_filter = (
        "status",
        "job_type",
        "work_mode",
        "experience_level",
        "created_at",
    )
    search_fields = ("title", "company", "location")
    prepopulated_fields = {"slug": ("title", "company")}
    ordering = ("-created_at",)
    readonly_fields = ("views_count", "applications_count", "created_at", "updated_at")

    fieldsets = (
        ("Basic Info", {
            "fields": ("title", "slug", "company", "company_logo")
        }),
        ("Job Details", {
            "fields": ("description", "requirements", "responsibilities")
        }),
        ("Job Properties", {
            "fields": ("location", "job_type", "work_mode", "experience_level", "status")
        }),
        ("Compensation", {
            "fields": ("salary_min", "salary_max", "salary_currency")
        }),
        ("Skills", {
            "fields": ("required_skills", "nice_to_have_skills", "experience_years")
        }),
        ("Meta", {
            "fields": ("posted_by", "application_deadline", "application_url")
        }),
        ("Stats", {
            "fields": ("views_count", "applications_count")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at")
        }),
    )


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "job",
        "applicant",
        "status",
        "match_score",
        "applied_at",
    )
    list_filter = ("status", "applied_at")
    search_fields = ("job__title", "applicant__email")
    readonly_fields = ("applied_at", "updated_at")


@admin.register(SavedJob)
class SavedJobAdmin(admin.ModelAdmin):
    list_display = ("user", "job", "saved_at")
    search_fields = ("user__email", "job__title")
    readonly_fields = ("saved_at",)