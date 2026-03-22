import os
from flask import Blueprint, request, jsonify, current_app, send_file
from ..database import db
from ..models import Candidate
from ..utils.file_handler import allowed_file, save_uploaded_file, extract_text_from_file, delete_file
from ..services.resume_parser import parse_resume

candidates_bp = Blueprint('candidates', __name__)


@candidates_bp.route('/', methods=['GET'])
def list_candidates():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '').strip()

    query = Candidate.query
    if search:
        query = query.filter(
            Candidate.name.ilike(f'%{search}%') |
            Candidate.email.ilike(f'%{search}%')
        )

    total = query.count()
    candidates = query.order_by(Candidate.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

    return jsonify({
        'candidates': [c.to_dict() for c in candidates],
        'total': total,
        'page': page,
        'pages': (total + per_page - 1) // per_page,
    })


@candidates_bp.route('/<int:candidate_id>', methods=['GET'])
def get_candidate(candidate_id):
    candidate = Candidate.query.get_or_404(candidate_id)
    return jsonify(candidate.to_dict())


@candidates_bp.route('/<int:candidate_id>/view', methods=['GET'])
def view_resume(candidate_id):
    """Serve the original resume file for viewing."""
    candidate = Candidate.query.get_or_404(candidate_id)
    if not candidate.file_path:
        return jsonify({'error': 'No file path stored for this candidate'}), 404

    try:
        fpath = candidate.file_path
        if not os.path.isabs(fpath):
            fpath = os.path.abspath(os.path.join(current_app.root_path, '..', fpath))

        # File doesn't exist on disk (e.g. manually seeded candidate)
        if not os.path.exists(fpath):
            html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Resume — {candidate.name or 'Candidate'}</title>
  <style>
    body {{ font-family: 'Inter', -apple-system, sans-serif; background:#0D1121; color:#EFF6FF;
           display:flex; align-items:center; justify-content:center; min-height:100vh; margin:0; }}
    .box {{ background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1);
            border-radius:20px; padding:48px; max-width:480px; text-align:center; }}
    .icon {{ font-size:56px; margin-bottom:16px; }}
    h2 {{ margin:0 0 8px; font-size:22px; color:#38BDF8; }}
    p  {{ color:#8B95B0; font-size:14px; line-height:1.6; margin:8px 0; }}
    .name {{ font-weight:700; color:#EFF6FF; font-size:18px; margin-bottom:4px; }}
    .badge {{ display:inline-block; padding:4px 12px; border-radius:999px; font-size:11px;
              font-weight:600; background:rgba(16,185,129,0.15); color:#34D399;
              border:1px solid rgba(16,185,129,0.3); margin-top:16px; }}
  </style>
</head>
<body>
  <div class="box">
    <div class="icon">📄</div>
    <div class="name">{candidate.name or 'Unknown Candidate'}</div>
    <h2>No Resume File Uploaded</h2>
    <p>This candidate was added directly to the system without an attached resume file.</p>
    <p>Email: <strong>{candidate.email or '—'}</strong><br>
       Experience: <strong>{candidate.experience_years or 0} years</strong><br>
       Skills: <strong>{', '.join((candidate.skills or [])[:6]) or '—'}</strong>
    </p>
    <span class="badge">✓ Profile Exists in Database</span>
  </div>
</body>
</html>"""
            from flask import Response
            return Response(html, mimetype='text/html')

        return send_file(fpath)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@candidates_bp.route('/upload', methods=['POST'])
def upload_resume():
    """Upload one or multiple resumes."""
    if 'files' not in request.files and 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    files = request.files.getlist('files') or [request.files.get('file')]
    results = []
    errors = []

    for file in files:
        if not file or file.filename == '':
            continue
        if not allowed_file(file.filename):
            errors.append(f'{file.filename}: Unsupported file type. Use PDF, DOCX, or TXT.')
            continue
        try:
            file_path, original_name, file_type = save_uploaded_file(file)
            raw_text = extract_text_from_file(file_path, file_type)

            if not raw_text or len(raw_text.strip()) < 50:
                delete_file(file_path)
                errors.append(f'{original_name}: Could not extract meaningful text from file.')
                continue

            parsed = parse_resume(raw_text)
            
            # Extract location heuristically from resume text
            location = _extract_location_from_text(raw_text)

            candidate = Candidate(
                name=parsed.get('name'),
                email=parsed.get('email'),
                phone=parsed.get('phone'),
                filename=original_name,
                file_path=file_path,
                file_type=file_type,
                raw_text=raw_text[:50000],  # Limit stored text
                experience_years=parsed.get('experience_years', 0.0),
                education_level=parsed.get('education_level'),
                location=location,
                summary=parsed.get('summary'),
            )
            candidate.skills = parsed.get('skills', [])
            candidate.job_titles = parsed.get('job_titles', [])

            db.session.add(candidate)
            db.session.commit()

            results.append({
                'candidate': candidate.to_dict(),
                'parsed': {
                    'name': parsed.get('name'),
                    'email': parsed.get('email'),
                    'skills_count': len(parsed.get('skills', [])),
                    'experience_years': parsed.get('experience_years'),
                    'education': parsed.get('education_level'),
                },
            })
        except Exception as e:
            current_app.logger.error(f"Error uploading {file.filename}: {e}")
            errors.append(f'{file.filename}: Upload failed - {str(e)}')

    if not results and errors:
        return jsonify({'error': 'All uploads failed', 'details': errors}), 400

    return jsonify({
        'uploaded': results,
        'errors': errors,
        'count': len(results),
    }), 201


@candidates_bp.route('/<int:candidate_id>', methods=['DELETE'])
def delete_candidate(candidate_id):
    candidate = Candidate.query.get_or_404(candidate_id)
    delete_file(candidate.file_path)
    db.session.delete(candidate)
    db.session.commit()
    return jsonify({'message': 'Candidate deleted successfully'})


@candidates_bp.route('/<int:candidate_id>/reparse', methods=['POST'])
def reparse_candidate(candidate_id):
    """Re-parse an existing candidate's resume."""
    candidate = Candidate.query.get_or_404(candidate_id)
    if not candidate.raw_text:
        return jsonify({'error': 'No raw text available for re-parsing'}), 400

    parsed = parse_resume(candidate.raw_text)
    candidate.name = parsed.get('name') or candidate.name
    candidate.email = parsed.get('email') or candidate.email
    candidate.phone = parsed.get('phone') or candidate.phone
    candidate.experience_years = parsed.get('experience_years', 0.0)
    candidate.education_level = parsed.get('education_level')
    candidate.location = _extract_location_from_text(candidate.raw_text) or candidate.location
    candidate.summary = parsed.get('summary')
    candidate.skills = parsed.get('skills', [])
    candidate.job_titles = parsed.get('job_titles', [])

    db.session.commit()
    return jsonify(candidate.to_dict())


def _extract_location_from_text(text):
    """Heuristically extract location from resume text."""
    import re
    if not text:
        return None
    
    # Check for Remote first
    if re.search(r'\b(remote|work from home|wfh)\b', text, re.IGNORECASE):
        return 'Remote'
    
    # Common Indian and international cities
    cities = [
        'bangalore', 'bengaluru', 'hyderabad', 'pune', 'mumbai', 'chennai',
        'delhi', 'new delhi', 'kolkata', 'ahmedabad', 'jaipur', 'surat',
        'kochi', 'coimbatore', 'noida', 'gurgaon', 'gurugram', 'indore',
        'nagpur', 'visakhapatnam', 'vadodara', 'bhubaneswar', 'lucknow',
        'new york', 'san francisco', 'london', 'toronto', 'sydney', 'dubai',
        'singapore', 'berlin', 'amsterdam',
    ]
    
    text_lower = text.lower()
    for city in cities:
        if city in text_lower:
            return city.title() + ', India' if city not in ('new york', 'san francisco', 'london', 'toronto', 'sydney', 'dubai', 'singapore', 'berlin', 'amsterdam') else city.title()
    
    return None
