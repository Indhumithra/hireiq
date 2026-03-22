from flask import Blueprint, request, jsonify
from ..database import db
from ..models import Job
from ..services.job_analyzer import analyze_job_description
from ..services.bias_detector import detect_bias

jobs_bp = Blueprint('jobs', __name__)


@jobs_bp.route('/', methods=['GET'])
def list_jobs():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status', 'all')
    search = request.args.get('search', '').strip()

    query = Job.query
    if status != 'all':
        query = query.filter_by(status=status)
    if search:
        query = query.filter(Job.title.ilike(f'%{search}%') | Job.department.ilike(f'%{search}%'))

    total = query.count()
    jobs = query.order_by(Job.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

    return jsonify({
        'jobs': [j.to_dict() for j in jobs],
        'total': total,
        'page': page,
        'pages': (total + per_page - 1) // per_page,
    })


@jobs_bp.route('/<int:job_id>', methods=['GET'])
def get_job(job_id):
    job = Job.query.get_or_404(job_id)
    return jsonify(job.to_dict())


@jobs_bp.route('/', methods=['POST'])
def create_job():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    title = data.get('title', '').strip()
    description = data.get('description', '').strip()
    if not title or not description:
        return jsonify({'error': 'Title and description are required'}), 400

    # Analyze the job description
    analysis = analyze_job_description(description)
    bias_result = detect_bias(description)

    job = Job(
        title=title,
        department=data.get('department', ''),
        location=data.get('location', ''),
        employment_type=data.get('employment_type', 'Full-time'),
        description=description,
        experience_years_min=data.get('experience_years_min', analysis['experience_years_min']),
        experience_years_max=data.get('experience_years_max', analysis['experience_years_max']),
        education_level=data.get('education_level', analysis['education_level']),
        salary_min=data.get('salary_min', 0),
        salary_max=data.get('salary_max', 0),
        status='active',
        bias_score=bias_result['score'],
    )
    # Use provided skills or extracted ones
    job.required_skills = data.get('required_skills') or analysis['required_skills']
    job.preferred_skills = data.get('preferred_skills') or analysis['preferred_skills']
    job.bias_flags = bias_result['flags']

    db.session.add(job)
    db.session.commit()

    return jsonify({
        'job': job.to_dict(),
        'analysis': analysis,
        'bias': bias_result,
    }), 201


@jobs_bp.route('/<int:job_id>', methods=['PUT'])
def update_job(job_id):
    job = Job.query.get_or_404(job_id)
    data = request.get_json()

    if 'title' in data:
        job.title = data['title']
    if 'department' in data:
        job.department = data['department']
    if 'location' in data:
        job.location = data['location']
    if 'employment_type' in data:
        job.employment_type = data['employment_type']
    if 'description' in data:
        job.description = data['description']
        # Re-analyze if description changed
        analysis = analyze_job_description(data['description'])
        bias_result = detect_bias(data['description'])
        job.required_skills = data.get('required_skills') or analysis['required_skills']
        job.preferred_skills = data.get('preferred_skills') or analysis['preferred_skills']
        job.bias_flags = bias_result['flags']
        job.bias_score = bias_result['score']
    if 'experience_years_min' in data:
        job.experience_years_min = data['experience_years_min']
    if 'experience_years_max' in data:
        job.experience_years_max = data['experience_years_max']
    if 'education_level' in data:
        job.education_level = data['education_level']
    if 'status' in data:
        job.status = data['status']

    db.session.commit()
    return jsonify(job.to_dict())


@jobs_bp.route('/<int:job_id>', methods=['DELETE'])
def delete_job(job_id):
    job = Job.query.get_or_404(job_id)
    db.session.delete(job)
    db.session.commit()
    return jsonify({'message': 'Job deleted successfully'})


@jobs_bp.route('/analyze', methods=['POST'])
def analyze_job():
    """Analyze a job description without saving it."""
    data = request.get_json()
    description = data.get('description', '')
    analysis = analyze_job_description(description)
    bias_result = detect_bias(description)
    return jsonify({'analysis': analysis, 'bias': bias_result})
