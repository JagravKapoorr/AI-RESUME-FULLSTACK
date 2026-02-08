from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.conf import settings
import os

from .models import ParsedResume, ProfileCompletion
from .services.resume_parser import ResumeParser
from .models import Job, JobApplication, SavedJob, ParsedResume
from django.core.paginator import Paginator
from django.db.models import Q

@login_required(login_url='accounts:login')
def upload_resume(request):
    """Upload resume and parse it"""
    
    if request.method == 'POST':
        resume_file = request.FILES.get('resume')
        
        # Validation
        if not resume_file:
            messages.error(request, "Please select a file to upload")
            return redirect('resumes:upload_resume')
        
        # Validate file type
        file_extension = resume_file.name.split('.')[-1].lower()
        if file_extension not in ['pdf', 'docx', 'doc']:
            messages.error(request, "Only PDF and DOCX files are supported")
            return redirect('resumes:upload_resume')
        
        # Validate file size (5MB max)
        if resume_file.size > 5 * 1024 * 1024:
            messages.error(request, "File size must be less than 5MB")
            return redirect('resumes:upload_resume')
        
        # Create ParsedResume instance
        parsed_resume = ParsedResume.objects.create(
            user=request.user,
            file=resume_file,
            original_filename=resume_file.name,
            status='pending'
        )
        
        # Process resume synchronously
        try:
            _process_resume(parsed_resume)
            messages.success(request, "✅ Resume uploaded and parsed successfully!")
            return redirect('resumes:resume_detail', pk=parsed_resume.pk)
        except Exception as e:
            messages.error(request, f"❌ Error processing resume: {str(e)}")
            return redirect('resumes:upload_resume')
    
    # GET request - show upload form
    context = {
        'existing_resumes': ParsedResume.objects.filter(user=request.user)[:5]
    }
    return render(request, 'upload_resume.html', context)


def _process_resume(parsed_resume: ParsedResume):
    """Process and parse the resume"""
    try:
        # Update status
        parsed_resume.status = 'processing'
        parsed_resume.save()
        
        # Initialize parser
        parser = ResumeParser()
        
        # Parse the resume
        resume_data = parser.parse_resume(
            file_path=parsed_resume.file.path,
            file_type=parsed_resume.file_extension,
            use_simple=True  # Use simple schema for faster/cheaper parsing
        )
        
        # Save parsed data
        parsed_resume.parsed_data = resume_data
        parsed_resume.skills = resume_data.get('skills', [])
        parsed_resume.experience_years = resume_data.get('total_experience_years', 0)
        
        # Get education level
        education = resume_data.get('education', [])
        if education:
            parsed_resume.education_level = education[0] if isinstance(education[0], str) else 'Not specified'
        
        parsed_resume.status = 'completed'
        parsed_resume.save()
        
        # Auto-fill user profile
        _update_user_profile(parsed_resume.user, resume_data)
        
        # Calculate profile completion
        _calculate_profile_completion(parsed_resume.user)
        
    except Exception as e:
        parsed_resume.status = 'failed'
        parsed_resume.error_message = str(e)
        parsed_resume.save()
        raise


def _update_user_profile(user, resume_data: dict):
    """Update user profile with parsed data"""
    
    # Update name if empty
    if resume_data.get('name') and not (user.first_name or user.last_name):
        name_parts = resume_data['name'].split()
        if name_parts:
            user.first_name = name_parts[0]
            user.last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
            user.save()
    
    # If you have a UserProfile model with additional fields:
    # try:
    #     profile = user.profile
    #     if not profile.phone and resume_data.get('phone'):
    #         profile.phone = resume_data['phone']
    #     if not profile.location and resume_data.get('location'):
    #         profile.location = resume_data['location']
    #     profile.save()
    # except:
    #     pass


def _calculate_profile_completion(user):
    """Calculate profile completion score"""
    
    # Required fields to check
    score = 0
    total_fields = 5
    missing = []
    suggestions = []
    
    # Check basic info
    if user.first_name and user.last_name:
        score += 20
    else:
        missing.append('name')
        suggestions.append('Complete your name')
    
    if user.email:
        score += 20
    else:
        missing.append('email')
        suggestions.append('Add your email address')
    
    # Check resume
    has_resume = user.resumes.filter(status='completed').exists()
    if has_resume:
        score += 30
        
        # Check if resume has skills
        latest_resume = user.resumes.filter(status='completed').first()
        if latest_resume and latest_resume.skill_count > 0:
            score += 15
        else:
            suggestions.append('Add more skills to your resume')
    else:
        missing.append('resume')
        suggestions.append('Upload your resume to boost your profile')
    
    # Check role
    if user.role:
        score += 15
    else:
        missing.append('role')
        suggestions.append('Select your role (Candidate/Recruiter)')
    
    # Update or create ProfileCompletion
    ProfileCompletion.objects.update_or_create(
        user=user,
        defaults={
            'completion_score': score,
            'missing_fields': missing,
            'suggestions': suggestions,
        }
    )


@login_required(login_url='accounts:login')
def resume_list(request):
    """List all user's resumes"""
    resumes = ParsedResume.objects.filter(user=request.user)
    
    context = {
        'resumes': resumes,
    }
    return render(request, 'resume_list.html', context)


@login_required(login_url='accounts:login')
def resume_detail(request, pk):
    """View detailed parsed resume"""
    resume = get_object_or_404(ParsedResume, pk=pk, user=request.user)
    
    context = {
        'resume': resume,
        'parsed_data': resume.parsed_data,
    }
    return render(request, 'resume_detail.html', context)


@login_required(login_url='accounts:login')
def delete_resume(request, pk):
    """Delete a resume"""
    resume = get_object_or_404(ParsedResume, pk=pk, user=request.user)
    
    if request.method == 'POST':
        # Delete the file from storage
        if resume.file and os.path.exists(resume.file.path):
            os.remove(resume.file.path)
        
        resume.delete()
        
        # Recalculate profile completion
        _calculate_profile_completion(request.user)
        
        messages.success(request, "Resume deleted successfully")
        return redirect('resumes:resume_list')
    
    context = {'resume': resume}
    return render(request, 'confirm_delete.html', context)


@login_required(login_url='accounts:login')
def profile_completion(request):
    """View profile completion status"""
    
    # Get or create profile completion
    completion, created = ProfileCompletion.objects.get_or_create(
        user=request.user,
        defaults={'completion_score': 0}
    )
    
    # Recalculate if it's old or requested
    if created or request.GET.get('refresh'):
        _calculate_profile_completion(request.user)
        completion.refresh_from_db()
    
    context = {
        'completion': completion,
    }
    return render(request, 'profile_completion.html', context)


# API Endpoints (for AJAX calls)

@login_required(login_url='accounts:login')
def api_resume_status(request, pk):
    """API: Get resume parsing status"""
    resume = get_object_or_404(ParsedResume, pk=pk, user=request.user)
    
    return JsonResponse({
        'status': resume.status,
        'error_message': resume.error_message,
        'is_completed': resume.is_completed,
    })


@login_required(login_url='accounts:login')
def api_profile_score(request):
    """API: Get profile completion score"""
    
    completion, _ = ProfileCompletion.objects.get_or_create(
        user=request.user,
        defaults={'completion_score': 0}
    )
    
    return JsonResponse({
        'completion_score': completion.completion_score,
        'missing_fields': completion.missing_fields,
        'suggestions': completion.suggestions,
    })


def browse_jobs(request):
    """Browse all jobs with filters and search"""
    
    # Get all active jobs
    jobs = Job.objects.filter(status='active')
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        jobs = jobs.filter(
            Q(title__icontains=search_query) |
            Q(company__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(location__icontains=search_query)
        )
    
    # Filters
    job_type = request.GET.get('job_type', '')
    if job_type:
        jobs = jobs.filter(job_type=job_type)
    
    work_mode = request.GET.get('work_mode', '')
    if work_mode:
        jobs = jobs.filter(work_mode=work_mode)
    
    experience_level = request.GET.get('experience_level', '')
    if experience_level:
        jobs = jobs.filter(experience_level=experience_level)
    
    location = request.GET.get('location', '')
    if location:
        jobs = jobs.filter(location__icontains=location)
    
    # Sorting
    sort_by = request.GET.get('sort', '-created_at')
    valid_sorts = ['-created_at', 'created_at', 'title', '-salary_max']
    if sort_by in valid_sorts:
        jobs = jobs.order_by(sort_by)
    
    # Get filter options for the sidebar
    filter_options = {
        'job_types': Job.objects.values_list('job_type', flat=True).distinct(),
        'work_modes': Job.objects.values_list('work_mode', flat=True).distinct(),
        'experience_levels': Job.objects.values_list('experience_level', flat=True).distinct(),
        'locations': Job.objects.values_list('location', flat=True).distinct()[:20],
    }
    
    # Pagination
    paginator = Paginator(jobs, 12)  # 12 jobs per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get saved jobs for current user
    saved_job_ids = []
    if request.user.is_authenticated:
        saved_job_ids = list(
            SavedJob.objects.filter(user=request.user).values_list('job_id', flat=True)
        )
    
    context = {
        'page_obj': page_obj,
        'jobs': page_obj,
        'total_jobs': paginator.count,
        'search_query': search_query,
        'filter_options': filter_options,
        'current_filters': {
            'job_type': job_type,
            'work_mode': work_mode,
            'experience_level': experience_level,
            'location': location,
            'sort': sort_by,
        },
        'saved_job_ids': saved_job_ids,
    }
    
    return render(request, 'browse_jobs.html', context)


def job_detail(request, slug):
    """View individual job details"""
    
    job = get_object_or_404(Job, slug=slug)
    
    # Increment view count
    job.increment_views()
    
    # Check if user has applied
    has_applied = False
    application = None
    if request.user.is_authenticated:
        application = JobApplication.objects.filter(
            job=job,
            applicant=request.user
        ).first()
        has_applied = application is not None
    
    # Check if job is saved
    is_saved = False
    if request.user.is_authenticated:
        is_saved = SavedJob.objects.filter(
            user=request.user,
            job=job
        ).exists()
    
    # Get similar jobs
    similar_jobs = Job.objects.filter(
        status='active',
        job_type=job.job_type
    ).exclude(id=job.id)[:4]
    
    # Get user's latest resume
    latest_resume = None
    if request.user.is_authenticated and request.user.role == 'candidate':
        latest_resume = ParsedResume.objects.filter(
            user=request.user,
            status='completed'
        ).first()
    
    context = {
        'job': job,
        'has_applied': has_applied,
        'application': application,
        'is_saved': is_saved,
        'similar_jobs': similar_jobs,
        'latest_resume': latest_resume,
    }
    
    return render(request, 'resumes/job_detail.html', context)


@login_required(login_url='accounts:login')
def apply_job(request, slug):
    """Apply for a job"""
    
    job = get_object_or_404(Job, slug=slug)
    
    # Check if user is a candidate
    if request.user.role != 'candidate':
        messages.error(request, "Only candidates can apply for jobs")
        return redirect('resumes:job_detail', slug=slug)
    
    # Check if already applied
    if JobApplication.objects.filter(job=job, applicant=request.user).exists():
        messages.warning(request, "You have already applied for this job")
        return redirect('resumes:job_detail', slug=slug)
    
    if request.method == 'POST':
        cover_letter = request.POST.get('cover_letter', '')
        resume_id = request.POST.get('resume_id')
        
        # Get resume
        resume = None
        if resume_id:
            resume = get_object_or_404(
                ParsedResume,
                id=resume_id,
                user=request.user,
                status='completed'
            )
        
        # Create application
        application = JobApplication.objects.create(
            job=job,
            applicant=request.user,
            resume=resume,
            cover_letter=cover_letter,
            status='pending'
        )
        
        # Calculate match score if resume exists
        if resume and resume.skills:
            matching_skills = list(set(resume.skills) & set(job.required_skills))
            missing_skills = list(set(job.required_skills) - set(resume.skills))
            
            # Simple match score calculation
            if job.required_skills:
                match_score = (len(matching_skills) / len(job.required_skills)) * 100
            else:
                match_score = 0
            
            application.match_score = round(match_score, 2)
            application.matching_skills = matching_skills
            application.missing_skills = missing_skills
            application.save()
        
        # Increment job applications count
        job.applications_count += 1
        job.save(update_fields=['applications_count'])
        
        messages.success(request, "Application submitted successfully! 🎉")
        return redirect('resumes:my_applications')
    
    # GET request - show application form
    resumes = ParsedResume.objects.filter(
        user=request.user,
        status='completed'
    )
    
    context = {
        'job': job,
        'resumes': resumes,
    }
    
    return render(request, 'resumes/apply_job.html', context)


@login_required(login_url='accounts:login')
def save_job(request, slug):
    """Save/unsave a job (bookmark)"""
    
    job = get_object_or_404(Job, slug=slug)
    
    saved_job, created = SavedJob.objects.get_or_create(
        user=request.user,
        job=job
    )
    
    if not created:
        # Already saved, so unsave it
        saved_job.delete()
        return JsonResponse({'saved': False, 'message': 'Job removed from saved'})
    
    return JsonResponse({'saved': True, 'message': 'Job saved successfully'})


@login_required(login_url='accounts:login')
def saved_jobs(request):
    """View all saved jobs"""
    
    saved = SavedJob.objects.filter(user=request.user).select_related('job')
    
    context = {
        'saved_jobs': saved,
    }
    
    return render(request, 'resumes/saved_jobs.html', context)


@login_required(login_url='accounts:login')
def my_applications(request):
    """View all job applications"""
    
    applications = JobApplication.objects.filter(
        applicant=request.user
    ).select_related('job', 'resume').order_by('-applied_at')
    
    # Get stats
    stats = {
        'total': applications.count(),
        'pending': applications.filter(status='pending').count(),
        'reviewed': applications.filter(status='reviewed').count(),
        'shortlisted': applications.filter(status='shortlisted').count(),
        'rejected': applications.filter(status='rejected').count(),
    }
    
    context = {
        'applications': applications,
        'stats': stats,
    }
    
    return render(request, 'resumes/my_applications.html', context)


@login_required(login_url='accounts:login')
def withdraw_application(request, application_id):
    """Withdraw a job application"""
    
    application = get_object_or_404(
        JobApplication,
        id=application_id,
        applicant=request.user
    )
    
    if request.method == 'POST':
        # Update status
        application.status = 'withdrawn'
        application.save()
        
        # Decrement job applications count
        job = application.job
        job.applications_count = max(0, job.applications_count - 1)
        job.save(update_fields=['applications_count'])
        
        messages.success(request, "Application withdrawn")
        return redirect('resumes:my_applications')
    
    context = {
        'application': application,
    }
    
    return render(request, 'resumes/withdraw_application.html', context)