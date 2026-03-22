import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app
import logging
import os

def send_shortlist_email(candidate_email, candidate_name, job_title):
    """Send an email to a shortlisted candidate."""
    if not candidate_email:
        logging.warning(f"No email found for candidate {candidate_name}. Skipping email.")
        return False

    config = current_app.config

    # Email Content Template
    subject = f"Career Update: Shortlisted for {job_title} | HireIQ"
    
    body_text = f"""
Dear {candidate_name},

Congratulations! We are pleased to inform you that following our AI-powered screening process, you have been shortlisted for the position of {job_title}.

Your profile stood out to our hiring team, and we are excited to move forward with your application. Our HR department will contact you within the next 48 hours to discuss the next steps and schedule an initial interview.

Please keep an eye on your inbox and phone for further updates.

Best regards,

The Recruitment Team
HireIQ Human Resources
"""

    body_html = f"""
    <html>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden;">
                <div style="background: linear-gradient(135deg, #0EA5E9, #10B981); padding: 30px; text-align: center; color: white;">
                    <h1 style="margin: 0; font-size: 24px;">Congratulations!</h1>
                </div>
                <div style="padding: 30px;">
                    <p>Dear <strong>{candidate_name}</strong>,</p>
                    <p>We are pleased to inform you that you have been <strong>shortlisted</strong> for the position of <strong>{job_title}</strong>.</p>
                    <p>Your qualifications and experience align closely with what we are looking for. Our hiring team has reviewed your application and is eager to discuss your potential fit within our organization.</p>
                    <div style="background: #f8fafc; border-radius: 6px; padding: 20px; margin: 20px 0; border-left: 4px solid #0EA5E9;">
                        <p style="margin:0;"><strong>Next Steps:</strong> Our HR department will reach out to you shortly to schedule an interview. Please ensure your contact details are up to date.</p>
                    </div>
                    <p>Thank you for choosing to grow your career with us.</p>
                    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                    <p style="color: #888; font-size: 14px;">Best regards,<br><strong>The Recruitment Team</strong><br>HireIQ HR Department</p>
                </div>
                <div style="background: #f9f9f9; padding: 15px; text-align: center; font-size: 12px; color: #aaa;">
                    This is an automated message from the HireIQ AI Screening System.
                </div>
            </div>
        </body>
    </html>
    """

    # Check if mail is configured
    if not all([config.get('MAIL_SERVER'), config.get('MAIL_USERNAME'), config.get('MAIL_PASSWORD')]):
        logging.warning("Mail settings not configured. Saving email to 'mail_sent_history/' for demo purposes.")
        
        try:
            mail_dir = os.path.join(current_app.root_path, '..', 'mail_sent_history')
            os.makedirs(mail_dir, exist_ok=True)
            
            filename = f"shortlist_{candidate_name.replace(' ', '_')}_{job_title.replace(' ', '_')}.html"
            with open(os.path.join(mail_dir, filename), 'w') as f:
                f.write(body_html)
                
            return True, "Sent (Demo Mode)"
        except Exception as e:
            return False, f"Mock Failed: {str(e)}"

    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = config.get('MAIL_DEFAULT_SENDER')
        msg['To'] = candidate_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body_text, 'plain'))
        msg.attach(MIMEText(body_html, 'html'))

        server = smtplib.SMTP(config.get('MAIL_SERVER'), config.get('MAIL_PORT'))
        if config.get('MAIL_USE_TLS'):
            server.starttls()
        
        server.login(config.get('MAIL_USERNAME'), config.get('MAIL_PASSWORD'))
        server.send_message(msg)
        server.quit()
        
        logging.info(f"Shortlist email sent successfully to {candidate_email}")
        return True, "Sent (SMTP)"

    except Exception as e:
        error_msg = str(e)
        logging.error(f"Failed to send shortlist email to {candidate_email}: {error_msg}")
        return False, f"Error: {error_msg[:50]}"

def send_rejection_email(candidate_email, candidate_name, job_title):
    """Send an email to a rejected candidate."""
    if not candidate_email:
        logging.warning(f"No email found for candidate {candidate_name}. Skipping email.")
        return False

    config = current_app.config

    subject = f"Update regarding your application for {job_title} | HireIQ"
    
    body_text = f"""
Dear {candidate_name},

Thank you for taking the time to apply for the {job_title} position.

While your background is impressive, we have decided to move forward with other candidates whose qualifications more closely align with the specific needs of this role at this time.

We appreciate your interest in joining our team and wish you the best of luck in your job search.

Best regards,

The Recruitment Team
HireIQ Human Resources
"""

    body_html = f"""
    <html>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden;">
                <div style="background: linear-gradient(135deg, #64748B, #475569); padding: 30px; text-align: center; color: white;">
                    <h1 style="margin: 0; font-size: 24px;">Application Update</h1>
                </div>
                <div style="padding: 30px;">
                    <p>Dear <strong>{candidate_name}</strong>,</p>
                    <p>Thank you for taking the time to apply for the <strong>{job_title}</strong> position.</p>
                    <p>While your background is impressive, we have decided to move forward with other candidates whose qualifications more closely match the specific needs of this role at this time.</p>
                    <p>We appreciate your interest in our team and wish you the best of luck in your continued job search.</p>
                    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                    <p style="color: #888; font-size: 14px;">Best regards,<br><strong>The Recruitment Team</strong><br>HireIQ HR Department</p>
                </div>
                <div style="background: #f9f9f9; padding: 15px; text-align: center; font-size: 12px; color: #aaa;">
                    This is an automated message from the HireIQ AI Screening System.
                </div>
            </div>
        </body>
    </html>
    """

    if not all([config.get('MAIL_SERVER'), config.get('MAIL_USERNAME'), config.get('MAIL_PASSWORD')]):
        try:
            mail_dir = os.path.join(current_app.root_path, '..', 'mail_sent_history')
            os.makedirs(mail_dir, exist_ok=True)
            filename = f"rejection_{candidate_name.replace(' ', '_')}_{job_title.replace(' ', '_')}.html"
            with open(os.path.join(mail_dir, filename), 'w') as f:
                f.write(body_html)
            return True, "Sent (Demo Mode)"
        except Exception as e:
            return False, f"Mock Failed: {str(e)}"

    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = config.get('MAIL_DEFAULT_SENDER')
        msg['To'] = candidate_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body_text, 'plain'))
        msg.attach(MIMEText(body_html, 'html'))

        server = smtplib.SMTP(config.get('MAIL_SERVER'), config.get('MAIL_PORT'))
        if config.get('MAIL_USE_TLS'):
            server.starttls()
        
        server.login(config.get('MAIL_USERNAME'), config.get('MAIL_PASSWORD'))
        server.send_message(msg)
        server.quit()
        return True, "Sent (SMTP)"
    except Exception as e:
        error_msg = str(e)
        return False, f"Error: {error_msg[:50]}"
