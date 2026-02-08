from django.db import models
from django.conf import settings
from django.utils.text import slugify


class ParsedResume(models.Model):
    """Store uploaded resumes and parsed data"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='resumes'
    )
    file = models.FileField(upload_to='resumes/%Y/%m/')
    original_filename = models.CharField(max_length=255)
    
    # Parsed data stored as JSON
    parsed_data = models.JSONField(default=dict, blank=True)
    
    # Quick access fields
    skills = models.JSONField(default=list, blank=True)
    experience_years = models.IntegerField(null=True, blank=True)
    education_level = models.CharField(max_length=100, null=True, blank=True)
    
    # Processing status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Parsed Resume'
        verbose_name_plural = 'Parsed Resumes'

    def __str__(self):
        return f"{self.user.email} - {self.original_filename}"
    
    @property
    def file_extension(self):
        """Get file extension"""
        return self.original_filename.split('.')[-1].lower() if self.original_filename else ''
    
    @property
    def is_completed(self):
        """Check if parsing is completed"""
        return self.status == 'completed'
    
    @property
    def skill_count(self):
        """Count of skills"""
        return len(self.skills) if self.skills else 0


class ProfileCompletion(models.Model):
    """Track user profile completion"""
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile_completion'
    )
    
    completion_score = models.IntegerField(default=0)  # 0-100
    missing_fields = models.JSONField(default=list, blank=True)
    suggestions = models.JSONField(default=list, blank=True)
    
    # Timestamps
    last_calculated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Profile Completion'
        verbose_name_plural = 'Profile Completions'

    def __str__(self):
        return f"{self.user.email} - {self.completion_score}%"

class Job(models.Model):
    """Job posting model"""
    
    JOB_TYPE_CHOICES = [
        ('full-time', 'Full Time'),
        ('part-time', 'Part Time'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
        ('freelance', 'Freelance'),
    ]
    
    EXPERIENCE_LEVEL_CHOICES = [
        ('entry', 'Entry Level'),
        ('mid', 'Mid Level'),
        ('senior', 'Senior Level'),
        ('lead', 'Lead'),
        ('executive', 'Executive'),
    ]
    
    WORK_MODE_CHOICES = [
        ('remote', 'Remote'),
        ('onsite', 'On-site'),
        ('hybrid', 'Hybrid'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('filled', 'Filled'),
    ]
    
    # Basic Information
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    company = models.CharField(max_length=200)
    company_logo = models.URLField(blank=True, null=True)
    
    # Job Details
    description = models.TextField()
    requirements = models.TextField()
    responsibilities = models.TextField()
    
    # Job Properties
    location = models.CharField(max_length=200)
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES, default='full-time')
    work_mode = models.CharField(max_length=20, choices=WORK_MODE_CHOICES, default='onsite')
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVEL_CHOICES, default='mid')
    
    # Compensation
    salary_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_currency = models.CharField(max_length=10, default='USD')
    
    # Skills & Requirements
    required_skills = models.JSONField(default=list, blank=True)
    nice_to_have_skills = models.JSONField(default=list, blank=True)
    experience_years = models.IntegerField(null=True, blank=True)
    
    # Meta Information
    posted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='posted_jobs'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Application Details
    application_deadline = models.DateField(null=True, blank=True)
    application_url = models.URLField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Stats
    views_count = models.IntegerField(default=0)
    applications_count = models.IntegerField(default=0)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Job'
        verbose_name_plural = 'Jobs'
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self):
        return f"{self.title} at {self.company}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(f"{self.title}-{self.company}")
            slug = base_slug
            counter = 1
            while Job.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
    
    @property
    def salary_range(self):
        """Get formatted salary range"""
        if self.salary_min and self.salary_max:
            return f"${self.salary_min:,.0f} - ${self.salary_max:,.0f}"
        elif self.salary_min:
            return f"From ${self.salary_min:,.0f}"
        elif self.salary_max:
            return f"Up to ${self.salary_max:,.0f}"
        return "Salary not specified"
    
    @property
    def is_active(self):
        """Check if job is active"""
        return self.status == 'active'
    
    def increment_views(self):
        """Increment view count"""
        self.views_count += 1
        self.save(update_fields=['views_count'])


class JobApplication(models.Model):
    """Job application model"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('shortlisted', 'Shortlisted'),
        ('interview', 'Interview'),
        ('offered', 'Offered'),
        ('rejected', 'Rejected'),
        ('accepted', 'Accepted'),
        ('withdrawn', 'Withdrawn'),
    ]
    
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='job_applications'
    )
    resume = models.ForeignKey(
        'ParsedResume', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='job_applications'
    )
    
    # Application Details
    cover_letter = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # AI Matching
    match_score = models.FloatField(null=True, blank=True)  # 0-100
    matching_skills = models.JSONField(default=list, blank=True)
    missing_skills = models.JSONField(default=list, blank=True)
    
    # Timestamps
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-applied_at']
        verbose_name = 'Job Application'
        verbose_name_plural = 'Job Applications'
        unique_together = ['job', 'applicant']  # Prevent duplicate applications

    def __str__(self):
        return f"{self.applicant.email} - {self.job.title}"


class SavedJob(models.Model):
    """Saved/bookmarked jobs"""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='saved_jobs'
    )
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='saved_by')
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-saved_at']
        verbose_name = 'Saved Job'
        verbose_name_plural = 'Saved Jobs'
        unique_together = ['user', 'job']

    def __str__(self):
        return f"{self.user.email} saved {self.job.title}"
