# ai_services/schemas.py

from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import List, Optional
from datetime import date


class WorkExperience(BaseModel):
    """Structured work experience entry"""
    company: str = Field(description="Company name")
    position: str = Field(description="Job title/position")
    location: Optional[str] = Field(None, description="Job location (city, state)")
    start_date: str = Field(description="Start date (e.g., 'Jan 2020', '2020-01')")
    end_date: str = Field(description="End date or 'Present'")
    description: Optional[str] = Field(None, description="Job responsibilities and achievements")
    achievements: List[str] = Field(default_factory=list, description="Key achievements or bullet points")
    
    @field_validator('end_date')
    def validate_end_date(cls, v):
        if not v:
            return 'Present'
        return v


class Education(BaseModel):
    """Structured education entry"""
    institution: str = Field(description="School/University name")
    degree: str = Field(description="Degree type (e.g., 'Bachelor of Science', 'Master of Arts')")
    field_of_study: Optional[str] = Field(None, description="Major/Field of study")
    location: Optional[str] = Field(None, description="Institution location")
    start_date: Optional[str] = Field(None, description="Start date")
    end_date: Optional[str] = Field(None, description="End date or 'Expected YYYY'")
    gpa: Optional[str] = Field(None, description="GPA if mentioned")
    honors: List[str] = Field(default_factory=list, description="Honors, awards, or distinctions")


class Certification(BaseModel):
    """Professional certifications"""
    name: str = Field(description="Certification name")
    issuing_organization: Optional[str] = Field(None, description="Issuing organization")
    issue_date: Optional[str] = Field(None, description="Date issued")
    expiry_date: Optional[str] = Field(None, description="Expiry date if applicable")
    credential_id: Optional[str] = Field(None, description="Credential ID or license number")


class Project(BaseModel):
    """Personal or professional projects"""
    name: str = Field(description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    technologies: List[str] = Field(default_factory=list, description="Technologies used")
    url: Optional[str] = Field(None, description="Project URL or GitHub link")
    date: Optional[str] = Field(None, description="Project date or duration")


class ResumeParsedSchema(BaseModel):
    """Enhanced schema for parsed resume data"""
    
    # Personal Information
    name: str = Field(description="Full name of the candidate")
    email: Optional[EmailStr] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    location: Optional[str] = Field(None, description="Current location (city, state/country)")
    linkedin: Optional[str] = Field(None, description="LinkedIn profile URL")
    github: Optional[str] = Field(None, description="GitHub profile URL")
    portfolio: Optional[str] = Field(None, description="Personal website or portfolio URL")
    
    # Professional Summary
    summary: Optional[str] = Field(None, description="Professional summary or objective statement")
    
    # Skills
    skills: List[str] = Field(default_factory=list, description="List of all skills")
    technical_skills: List[str] = Field(default_factory=list, description="Technical/hard skills")
    soft_skills: List[str] = Field(default_factory=list, description="Soft skills")
    
    # Experience
    experience: List[WorkExperience] = Field(default_factory=list, description="Work experience entries")
    total_experience_years: Optional[int] = Field(None, description="Total years of professional experience")
    
    # Education
    education: List[Education] = Field(default_factory=list, description="Education entries")
    highest_education: Optional[str] = Field(None, description="Highest level of education")
    
    # Certifications
    certifications: List[Certification] = Field(default_factory=list, description="Professional certifications")
    
    # Projects
    projects: List[Project] = Field(default_factory=list, description="Notable projects")
    
    # Languages
    languages: List[str] = Field(default_factory=list, description="Languages spoken")
    
    # Additional Information
    awards: List[str] = Field(default_factory=list, description="Awards and honors")
    publications: List[str] = Field(default_factory=list, description="Publications or papers")
    volunteer_work: List[str] = Field(default_factory=list, description="Volunteer experience")
    
    @field_validator('phone')
    def clean_phone(cls, v):
        """Clean phone number format"""
        if v:
            # Remove common formatting characters
            return ''.join(filter(str.isdigit, v))
        return v
    
    @field_validator('skills', 'technical_skills', 'soft_skills')
    def clean_skills(cls, v):
        """Remove duplicates and empty strings from skills"""
        if v:
            # Remove empty strings and duplicates while preserving order
            seen = set()
            cleaned = []
            for skill in v:
                skill_clean = skill.strip()
                if skill_clean and skill_clean.lower() not in seen:
                    seen.add(skill_clean.lower())
                    cleaned.append(skill_clean)
            return cleaned
        return []


# Alternative: Simpler schema (your original enhanced version)
class SimpleResumeParsedSchema(BaseModel):
    """Simplified schema for basic resume parsing"""
    name: str = Field(description="Full name")
    email: Optional[EmailStr] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    location: Optional[str] = Field(None, description="Location")
    summary: Optional[str] = Field(None, description="Professional summary")
    
    skills: List[str] = Field(default_factory=list, description="All skills")
    experience: List[str] = Field(default_factory=list, description="Work experience as text entries")
    education: List[str] = Field(default_factory=list, description="Education as text entries")
    
    total_experience_years: Optional[int] = Field(None, description="Years of experience")


# Schema for profile completion analysis
class ProfileCompletionSchema(BaseModel):
    """Schema for profile completion analysis"""
    completion_percentage: int = Field(description="Profile completion percentage (0-100)")
    completed_sections: List[str] = Field(description="Sections that are completed")
    missing_sections: List[str] = Field(description="Sections that are missing or incomplete")
    suggestions: List[str] = Field(description="Specific suggestions to improve profile")
    strengths: List[str] = Field(description="Profile strengths")
    priority_actions: List[str] = Field(description="Top 3 actions to improve profile")


# Schema for skill analysis
class SkillAnalysisSchema(BaseModel):
    """Schema for analyzing skills from resume"""
    
    class SkillCategory(BaseModel):
        category: str = Field(description="Skill category name")
        skills: List[str] = Field(description="Skills in this category")
        proficiency_level: Optional[str] = Field(None, description="Estimated proficiency level")
    
    skill_categories: List[SkillCategory] = Field(description="Categorized skills")
    trending_skills: List[str] = Field(default_factory=list, description="Skills that are currently in demand")
    recommended_skills: List[str] = Field(default_factory=list, description="Skills to learn based on current skillset")
    skill_gaps: List[str] = Field(default_factory=list, description="Important skills that are missing")


# Schema for job matching
class JobMatchSchema(BaseModel):
    """Schema for AI job matching results"""
    match_score: float = Field(description="Match score from 0-100")
    matching_skills: List[str] = Field(description="Skills that match the job requirements")
    missing_skills: List[str] = Field(description="Skills required but not in candidate's resume")
    experience_match: bool = Field(description="Whether experience level matches")
    education_match: bool = Field(description="Whether education level matches")
    explanation: str = Field(description="AI explanation of the match")
    recommendation: str = Field(description="AI recommendation (apply, maybe, skip)")
    improvement_suggestions: List[str] = Field(default_factory=list, description="How to improve match score")