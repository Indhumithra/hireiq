from flask import Blueprint, jsonify
from ..models import Job, Candidate, ScreeningResult
from ..database import db
from sqlalchemy import func
from datetime import datetime, timedelta, timezone

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get overview statistics for the dashboard."""
    total_jobs = Job.query.count()
    active_jobs = Job.query.filter_by(status='active').count()
    total_candidates = Candidate.query.count()
    total_screenings = ScreeningResult.query.count()
    shortlisted = ScreeningResult.query.filter_by(status='shortlisted')
    shortlisted_count = shortlisted.count()
    rejected = ScreeningResult.query.filter_by(status='rejected').count()
    pending = ScreeningResult.query.filter_by(status='pending').count()
    
    # Grab the top 3 most recently shortlisted candidates for the dashboard
    recent_shortlisted = shortlisted.order_by(ScreeningResult.screened_at.desc()).limit(3).all()
    shortlisted_info = []
    for s in recent_shortlisted:
        shortlisted_info.append({
            'name': s.candidate.name if s.candidate else 'Unknown',
            'job': s.job.title if s.job else 'Unknown Role',
            'score': s.overall_score
        })

    avg_score_result = db.session.query(func.avg(ScreeningResult.overall_score)).scalar()
    avg_score = round(float(avg_score_result), 1) if avg_score_result else 0.0

    # Bias analysis
    avg_bias = db.session.query(func.avg(Job.bias_score)).scalar()
    avg_bias = round(float(avg_bias), 1) if avg_bias else 0.0

    # Jobs with high bias
    high_bias_jobs = Job.query.filter(Job.bias_score >= 30).count()

    return jsonify({
        'jobs': {
            'total': total_jobs,
            'active': active_jobs,
            'closed': total_jobs - active_jobs,
        },
        'candidates': {
            'total': total_candidates,
        },
        'screenings': {
            'total': total_screenings,
            'shortlisted': shortlisted_count,
            'rejected': rejected,
            'pending': pending,
            'shortlist_rate': round(shortlisted_count / total_screenings * 100, 1) if total_screenings else 0,
            'avg_score': avg_score,
            'shortlisted_info': shortlisted_info
        },
        'bias': {
            'avg_bias_score': avg_bias,
            'high_bias_jobs': high_bias_jobs,
        },
    })


@dashboard_bp.route('/recent', methods=['GET'])
def get_recent():
    """Get recent activity for the dashboard."""
    recent_candidates = (
        Candidate.query.order_by(Candidate.created_at.desc()).limit(5).all()
    )
    recent_jobs = (
        Job.query.order_by(Job.created_at.desc()).limit(5).all()
    )
    
    # Limit to 20 recent screenings to avoid N+1 query explosion
    recent_screenings = (
        ScreeningResult.query
        .order_by(ScreeningResult.screened_at.desc())
        .limit(20)
        .all()
    )

    return jsonify({
        'recent_candidates': [c.to_dict() for c in recent_candidates],
        'recent_jobs': [j.to_dict() for j in recent_jobs],
        'recent_screenings': [s.to_dict() for s in recent_screenings],
    })


@dashboard_bp.route('/job-stats/<int:job_id>', methods=['GET'])
def get_job_stats(job_id):
    """Detailed stats for a specific job posting."""
    job = Job.query.get_or_404(job_id)
    results = ScreeningResult.query.filter_by(job_id=job_id).all()

    if not results:
        return jsonify({'job': job.to_dict(), 'stats': {}, 'score_distribution': []})

    scores = [r.overall_score for r in results]
    score_distribution = [0] * 10  # 0-9, 10-19, ..., 90-100
    for s in scores:
        bucket = min(int(s // 10), 9)
        score_distribution[bucket] += 1

    return jsonify({
        'job': job.to_dict(),
        'stats': {
            'total': len(results),
            'shortlisted': sum(1 for r in results if r.status == 'shortlisted'),
            'pending': sum(1 for r in results if r.status == 'pending'),
            'rejected': sum(1 for r in results if r.status == 'rejected'),
            'avg_score': round(sum(scores) / len(scores), 1),
            'max_score': round(max(scores), 1),
            'min_score': round(min(scores), 1),
        },
        'score_distribution': [
            {'range': f'{i*10}-{i*10+9}', 'count': score_distribution[i]}
            for i in range(10)
        ],
        'top_candidates': [
            r.to_dict() for r in sorted(results, key=lambda x: x.overall_score, reverse=True)[:5]
        ],
    })


@dashboard_bp.route('/skills-gap', methods=['GET'])
def skills_gap():
    """Analyze overall skills gap across all jobs."""
    jobs = Job.query.filter_by(status='active').all()
    all_required = {}
    for job in jobs:
        for skill in job.required_skills:
            all_required[skill] = all_required.get(skill, 0) + 1

    candidates = Candidate.query.all()
    all_candidate_skills = {}
    for c in candidates:
        for skill in c.skills:
            all_candidate_skills[skill] = all_candidate_skills.get(skill, 0) + 1

    # Top demanded vs available
    top_demanded = sorted(all_required.items(), key=lambda x: x[1], reverse=True)[:15]
    gap_analysis = []
    for skill, demand in top_demanded:
        supply = all_candidate_skills.get(skill, 0)
        gap_analysis.append({
            'skill': skill,
            'demand': demand,
            'supply': supply,
            'gap': max(demand - supply, 0),
        })

    return jsonify({'skills_gap': gap_analysis})
