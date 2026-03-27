from flask import Blueprint, render_template
from models import JobCard

public_bp = Blueprint('public', __name__)

@public_bp.route('/status/<qr_token>')
def status(qr_token):
    job = JobCard.query.filter_by(qr_token=qr_token).first_or_404()
    return render_template('jobs/status_public.html', job=job)
