import os
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content, HtmlContent

def get_avatar_url(user):
    """
    Get avatar URL for a user, falling back to default avatar
    
    Args:
        user: User instance
    
    Returns:
        str: Avatar URL or default avatar path
    """
    if user.avatar:
        return user.avatar.url
    return 'defaults/avatar-default.png'

def validate_avatar_file(file):
    """Validate avatar file upload"""
    # Check file size (max 5MB)
    if file.size > 5 * 1024 * 1024:
        return False
    
    # Check file extension
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    file_extension = os.path.splitext(file.name)[1].lower()
    
    if file_extension not in allowed_extensions:
        return False
    
    return True


def send_email_with_sendgrid(to_email, subject, html_content, text_content=None, from_email=None, from_name=None):
    """
    Send email using SendGrid API following official guide
    """
    try:
        # Use settings or defaults
        from_email = from_email or settings.SENDGRID_FROM_EMAIL
        from_name = from_name or settings.SENDGRID_FROM_NAME
        
        # Create SendGrid client
        sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
        
        # Create email following SendGrid guide
        from_email_obj = Email(from_email, from_name)
        to_email_obj = To(to_email)
        
        # Create content objects
        html_content_obj = HtmlContent(html_content)
        
        # Create mail object
        mail = Mail(from_email_obj, to_email_obj, subject, html_content_obj)
        
        # Add text content if provided
        if text_content:
            text_content_obj = Content("text/plain", text_content)
            mail.add_content(text_content_obj)
        
        # Send email
        response = sg.send(mail)
        
        # Check response status codes
        if response.status_code in [200, 201, 202]:
            print(f"Email sent successfully to {to_email}")
            print(f"SendGrid Response Status: {response.status_code}")
            return True
        else:
            print(f"Failed to send email. Status code: {response.status_code}")
            print(f"Response body: {response.body}")
            return False
            
    except Exception as e:
        print(f"Error sending email with SendGrid: {str(e)}")
        return False


def send_email_with_django(to_email, subject, html_content, text_content=None, from_email=None):
    """
    Send email using Django's email backend (fallback)
    """
    try:
        from_email = from_email or settings.FROM_EMAIL
        
        msg = EmailMultiAlternatives(
            subject=subject,
            from_email=from_email,
            to=[to_email],
            body=text_content or html_content
        )
        
        if html_content:
            msg.attach_alternative(html_content, "text/html")
        
        msg.send()
        print(f"Email sent successfully to {to_email} via Django")
        return True
        
    except Exception as e:
        print(f"Error sending email with Django: {str(e)}")
        return False


def send_password_reset_email(user, otp):
    """
    Send password reset email using SendGrid or Django fallback
    """
    context = {
        "otp": otp,
        "user_name": user.username
    }
    
    subject = "Vauice Sports App - Password Reset OTP"
    text_body = render_to_string("email/password_reset.txt", context)
    html_body = render_to_string("email/password_reset.html", context)
    
    # Try SendGrid first, fallback to Django
    if hasattr(settings, 'SENDGRID_API_KEY') and settings.SENDGRID_API_KEY:
        success = send_email_with_sendgrid(
            to_email=user.email,
            subject=subject,
            html_content=html_body,
            text_content=text_body
        )
    else:
        success = send_email_with_django(
            to_email=user.email,
            subject=subject,
            html_content=html_body,
            text_content=text_body
        )
    
    return success 