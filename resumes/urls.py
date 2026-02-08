# ai_services/urls.py

from django.urls import path
from . import views

app_name = 'resumes'

urlpatterns = [
    # Resume Management
    path('upload-resume/', views.upload_resume, name='upload_resume'),
    path('resumes/', views.resume_list, name='resume_list'),
    path('resume/<int:pk>/', views.resume_detail, name='resume_detail'),
    path('resume/<int:pk>/delete/', views.delete_resume, name='delete_resume'),
    
    # Profile Completion
    path('profile-completion/', views.profile_completion, name='profile_completion'),
    
    # API Endpoints
    path('api/resume/<int:pk>/status/', views.api_resume_status, name='api_resume_status'),
    path('api/profile-score/', views.api_profile_score, name='api_profile_score'),

# Job Browsing (NEW)
    path('jobs/', views.browse_jobs, name='browse_jobs'),
    path('jobs/<slug:slug>/', views.job_detail, name='job_detail'),
    path('jobs/<slug:slug>/apply/', views.apply_job, name='apply_job'),
    path('jobs/<slug:slug>/save/', views.save_job, name='save_job'),
    
    # Job Applications (NEW)
    path('my-applications/', views.my_applications, name='my_applications'),
    path('application/<int:application_id>/withdraw/', views.withdraw_application, name='withdraw_application'),
    
    # Saved Jobs (NEW)
    path('saved-jobs/', views.saved_jobs, name='saved_jobs'),
    
    # API Endpoints
    path('api/resume/<int:pk>/status/', views.api_resume_status, name='api_resume_status'),
    path('api/profile-score/', views.api_profile_score, name='api_profile_score'),
]

