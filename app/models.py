from datetime import datetime, timezone
from .database import db
import json


class Job(db.Model):
    __tablename__ = 'jobs'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    department = db.Column(db.String(100))
    location = db.Column(db.String(100))
    employment_type = db.Column(db.String(50), default='Full-time')
    description = db.Column(db.Text, nullable=False)
    required_skills_json = db.Column(db.Text, default='[]')
    preferred_skills_json = db.Column(db.Text, default='[]')
    experience_years_min = db.Column(db.Integer, default=0)
    experience_years_max = db.Column(db.Integer, default=10)
    education_level = db.Column(db.String(50), default='Bachelor')
    salary_min = db.Column(db.Integer, default=0)
    salary_max = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='active')  # active, closed
    bias_flags_json = db.Column(db.Text, default='[]')
    bias_score = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    screenings = db.relationship('ScreeningResult', backref='job', lazy=True,
                                  cascade='all, delete-orphan')

    @property
    def required_skills(self):
        return json.loads(self.required_skills_json or '[]')

    @required_skills.setter
    def required_skills(self, value):
        self.required_skills_json = json.dumps(value)

    @property
    def preferred_skills(self):
        return json.loads(self.preferred_skills_json or '[]')

    @preferred_skills.setter
    def preferred_skills(self, value):
        self.preferred_skills_json = json.dumps(value)

    @property
    def bias_flags(self):
        return json.loads(self.bias_flags_json or '[]')

    @bias_flags.setter
    def bias_flags(self, value):
        self.bias_flags_json = json.dumps(value)

    @property
    def job_level(self):
        if self.experience_years_min >= 5:
            return 'Senior'
        if self.experience_years_min == 0:
            return 'Fresher/Entry-Level'
        return 'Mid-Level'

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'department': self.department,
            'location': self.location,
            'employment_type': self.employment_type,
            'description': self.description,
            'required_skills': self.required_skills,
            'preferred_skills': self.preferred_skills,
            'experience_years_min': self.experience_years_min,
            'experience_years_max': self.experience_years_max,
            'education_level': self.education_level,
            'salary_min': self.salary_min,
            'salary_max': self.salary_max,
            'status': self.status,
            'job_level': self.job_level,
            'bias_flags': self.bias_flags,
            'bias_score': self.bias_score,
            'candidate_count': len(self.screenings),
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Candidate(db.Model):
    __tablename__ = 'candidates'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    email = db.Column(db.String(200))
    phone = db.Column(db.String(50))
    filename = db.Column(db.String(300), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(20))
    raw_text = db.Column(db.Text)
    skills_json = db.Column(db.Text, default='[]')
    experience_years = db.Column(db.Float, default=0.0)
    education_level = db.Column(db.String(50))
    location = db.Column(db.String(100))
    job_titles_json = db.Column(db.Text, default='[]')
    summary = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    screenings = db.relationship('ScreeningResult', backref='candidate', lazy=True,
                                  cascade='all, delete-orphan')

    @property
    def skills(self):
        return json.loads(self.skills_json or '[]')

    @skills.setter
    def skills(self, value):
        self.skills_json = json.dumps(value)

    @property
    def job_titles(self):
        return json.loads(self.job_titles_json or '[]')

    @job_titles.setter
    def job_titles(self, value):
        self.job_titles_json = json.dumps(value)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name or 'Unknown',
            'email': self.email,
            'phone': self.phone,
            'filename': self.filename,
            'file_type': self.file_type,
            'skills': self.skills,
            'experience_years': self.experience_years,
            'education_level': self.education_level,
            'location': self.location,
            'job_titles': self.job_titles,
            'summary': self.summary,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class ScreeningResult(db.Model):
    __tablename__ = 'screening_results'

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False)

    # Scores
    overall_score = db.Column(db.Float, default=0.0)
    semantic_score = db.Column(db.Float, default=0.0)
    skill_match_score = db.Column(db.Float, default=0.0)
    experience_score = db.Column(db.Float, default=0.0)
    education_score = db.Column(db.Float, default=0.0)
    location_score = db.Column(db.Float, default=0.0)

    # Details
    matched_skills_json = db.Column(db.Text, default='[]')
    missing_skills_json = db.Column(db.Text, default='[]')
    rank = db.Column(db.Integer, default=0)
    status = db.Column(db.String(30), default='pending')  # pending, shortlisted, rejected
    explanation = db.Column(db.Text)
    email_sent = db.Column(db.Boolean, default=False)
    email_status = db.Column(db.String(100), default='Not Sent')
    screened_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    @property
    def matched_skills(self):
        return json.loads(self.matched_skills_json or '[]')

    @matched_skills.setter
    def matched_skills(self, value):
        self.matched_skills_json = json.dumps(value)

    @property
    def missing_skills(self):
        return json.loads(self.missing_skills_json or '[]')

    @missing_skills.setter
    def missing_skills(self, value):
        self.missing_skills_json = json.dumps(value)

    def to_dict(self):
        return {
            'id': self.id,
            'job_id': self.job_id,
            'job_title': self.job.title if self.job else 'Unknown Role',
            'candidate_id': self.candidate_id,
            'candidate': self.candidate.to_dict() if self.candidate else None,
            'overall_score': round(self.overall_score or 0.0, 1),
            'semantic_score': round(self.semantic_score or 0.0, 1),
            'skill_match_score': round(self.skill_match_score or 0.0, 1),
            'experience_score': round(self.experience_score or 0.0, 1),
            'education_score': round(self.education_score or 0.0, 1),
            'location_score': round(self.location_score or 0.0, 1),
            'matched_skills': self.matched_skills,
            'missing_skills': self.missing_skills,
            'rank': self.rank,
            'status': self.status,
            'explanation': self.explanation,
            'email_sent': self.email_sent,
            'email_status': self.email_status,
            'screened_at': self.screened_at.isoformat() if self.screened_at else None,
        }
