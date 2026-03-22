from flask import Blueprint, request, jsonify, current_app
from ..database import db
from ..models import Job, Candidate, ScreeningResult
from ..services.ranker import rank_candidates
from ..utils.email_utils import send_shortlist_email, send_rejection_email

screening_bp = Blueprint('screening', __name__)


@screening_bp.route('/screen', methods=['POST'])
def screen_candidates():
    """
    Screen all candidates (or a subset) against a specific job.
    Also handles re-screening an already-screened job.
    """
    data = request.get_json()
    job_id = data.get('job_id')
    candidate_ids = data.get('candidate_ids')  # Optional: screen specific candidates only

    if not job_id:
        return jsonify({'error': 'job_id is required'}), 400

    job = Job.query.get_or_404(job_id)

    # Fetch candidates
    if candidate_ids:
        candidates = Candidate.query.filter(Candidate.id.in_(candidate_ids)).all()
    else:
        candidates = Candidate.query.all()

    if not candidates:
        return jsonify({'error': 'No candidates found to screen'}), 400

    # Delete existing screening results for this job if re-screening
    if data.get('refresh', False) or not candidate_ids:
        ScreeningResult.query.filter_by(job_id=job_id).delete()
        db.session.commit()

    # Build candidates data list
    candidates_data = [{'candidate': c, 'parsed_resume': {
        'skills': c.skills,
        'experience_years': c.experience_years,
        'education_level': c.education_level,
        'job_titles': c.job_titles,
    }} for c in candidates]

    # Run ranking engine
    custom_weights = data.get('weights')
    ranked_results = rank_candidates(job, candidates_data, weights=custom_weights)

    # Save results to database
    saved_results = []
    for result in ranked_results:
        candidate = result['candidate']

        # Check if screening result already exists (in case of partial re-screen)
        existing = ScreeningResult.query.filter_by(
            job_id=job_id, candidate_id=candidate.id
        ).first()

        if existing:
            sr = existing
        else:
            sr = ScreeningResult(job_id=job_id, candidate_id=candidate.id)
            db.session.add(sr)

        previous_status = sr.status if existing else None

        sr.overall_score = result['overall_score']
        sr.semantic_score = result['semantic_score']
        sr.skill_match_score = result['skill_match_score']
        sr.experience_score = result['experience_score']
        sr.education_score = result['education_score']
        sr.location_score = result['location_score']
        sr.matched_skills = result['matched_skills']
        sr.missing_skills = result['missing_skills']
        sr.rank = result['rank']
        sr.status = result['status']
        sr.explanation = result['explanation']

        # Send email only when transitioning INTO shortlisted for the first time
        newly_shortlisted = (sr.status == 'shortlisted' and 
                             previous_status != 'shortlisted' and
                             not sr.email_sent)
        if newly_shortlisted:
            success, msg = send_shortlist_email(candidate.email, candidate.name, job.title)
            sr.email_sent = success
            sr.email_status = msg

        saved_results.append(sr)

    db.session.commit()

    return jsonify({
        'job_id': job_id,
        'job_title': job.title,
        'total_screened': len(ranked_results),
        'shortlisted': sum(1 for r in ranked_results if r['status'] == 'shortlisted'),
        'results': [sr.to_dict() for sr in saved_results],
    })


@screening_bp.route('/results/<int:job_id>', methods=['GET'])
def get_results(job_id):
    """Get screening results for a job, sorted by rank."""
    job = Job.query.get_or_404(job_id)
    status_filter = request.args.get('status')

    query = ScreeningResult.query.filter_by(job_id=job_id)
    if status_filter:
        query = query.filter_by(status=status_filter)

    results = query.order_by(ScreeningResult.rank).all()

    return jsonify({
        'job': job.to_dict(),
        'results': [r.to_dict() for r in results],
        'stats': {
            'total': len(results),
            'shortlisted': sum(1 for r in results if r.status == 'shortlisted'),
            'pending': sum(1 for r in results if r.status == 'pending'),
            'rejected': sum(1 for r in results if r.status == 'rejected'),
            'avg_score': round(
                sum(r.overall_score for r in results) / len(results), 1
            ) if results else 0,
        },
    })


@screening_bp.route('/results/<int:job_id>/candidate/<int:candidate_id>', methods=['PATCH'])
def update_status(job_id, candidate_id):
    """Manually update a candidate's screening status (HR override)."""
    data = request.get_json()
    new_status = data.get('status')
    if new_status not in ('shortlisted', 'pending', 'rejected'):
        return jsonify({'error': 'Invalid status'}), 400

    result = ScreeningResult.query.filter_by(
        job_id=job_id, candidate_id=candidate_id
    ).first_or_404()

    if new_status == 'shortlisted' and result.status != 'shortlisted':
        success, msg = send_shortlist_email(result.candidate.email, result.candidate.name, result.job.title)
        result.email_sent = success
        result.email_status = msg
    elif new_status == 'rejected' and result.status != 'rejected':
        success, msg = send_rejection_email(result.candidate.email, result.candidate.name, result.job.title)
        result.email_sent = success
        result.email_status = msg

    result.status = new_status
    db.session.commit()
    return jsonify(result.to_dict())


@screening_bp.route('/results/<int:job_id>/export/csv', methods=['GET'])
def export_results_csv(job_id):
    """Export screening results for a job as a CSV file."""
    import pandas as pd
    import io
    from flask import Response

    job = Job.query.get_or_404(job_id)
    results = ScreeningResult.query.filter_by(job_id=job_id).order_by(ScreeningResult.rank).all()

    if not results:
        return jsonify({'error': 'No results to export'}), 404

    data = []
    for r in results:
        c = r.candidate
        data.append({
            'Rank': r.rank,
            'Name': c.name or 'Unknown',
            'Email': c.email or '',
            'Overall Score (%)': r.overall_score,
            'Semantic Match': r.semantic_score,
            'Skill Score': r.skill_match_score,
            'Experience Score': r.experience_score,
            'Education Score': r.education_score,
            'Status': r.status,
            'Matched Skills': ', '.join(r.matched_skills),
            'Missing Skills': ', '.join(r.missing_skills),
            'AI Explanation': r.explanation
        })

    df = pd.DataFrame(data)
    output = io.BytesIO()
    df.to_csv(output, index=False)
    output.seek(0)

    filename = f"HireIQ_Report_Job_{job_id}_{job.title.replace(' ', '_')}.csv"
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={filename}"}
    )
