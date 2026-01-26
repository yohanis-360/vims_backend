"""
Utility functions for user management.
"""
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def send_temporary_password_email(user, temporary_password, max_retries=3):
    """
    Send temporary password to admin email with retry mechanism.
    
    Args:
        user: User object
        temporary_password: The temporary password string
        max_retries: Maximum number of retry attempts (default: 3)
    """
    import time
    
    recipient_email = getattr(settings, 'ADMIN_EMAIL', 'tayeyohanis8@gmail.com')
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'tayeyohanis8@gmail.com')
    
    subject = f'New Inspector User Created - Temporary Password: {user.username}'
    
    message = f"""
A new inspector user has been created in the VIMS system.

User Details:
- User ID: {user.user_id}
- Username: {user.username}
- Full Name: {user.full_name}
- Email: {user.email}
- Phone: {user.phone or 'N/A'}

TEMPORARY PASSWORD: {temporary_password}

Please share this temporary password with the inspector. They will be required to change it on their first login.

This is an automated message from the VIMS system.
"""
    
    # Retry mechanism for network issues
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"[EMAIL] Attempt {attempt}/{max_retries}: Sending temporary password email for user {user.username}")
            logger.info(f"[EMAIL] From: {from_email}, To: {recipient_email}")
            
            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=[recipient_email],
                fail_silently=False,
            )
            
            logger.info(f"[EMAIL] ✓ Temporary password email sent successfully to {recipient_email} for user {user.username}")
            return True
            
        except Exception as e:
            logger.warning(f"[EMAIL] Attempt {attempt}/{max_retries} failed: {str(e)}")
            if attempt < max_retries:
                wait_time = attempt * 2  # Exponential backoff: 2s, 4s, 6s
                logger.info(f"[EMAIL] Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.error(f"[EMAIL] ✗ Failed to send email after {max_retries} attempts: {str(e)}", exc_info=True)
                # Don't raise exception - email failure shouldn't block user creation
                return False
    
    return False


def send_password_reset_email(user, reset_token, max_retries=3):
    """
    Send password reset email to user with reset link.
    
    Args:
        user: User object
        reset_token: The password reset token string
        max_retries: Maximum number of retry attempts (default: 3)
    """
    import time
    
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'tayeyohanis8@gmail.com')
    recipient_email = user.email
    
    # Get frontend URL from settings (default to localhost)
    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
    reset_link = f"{frontend_url}/reset-password?token={reset_token}"
    
    subject = 'VIMS - Password Reset Request'
    
    message = f"""
Hello {user.full_name},

You have requested to reset your password for your VIMS account.

Username: {user.username}
Email: {user.email}

To reset your password, please click on the following link:
{reset_link}

This link will expire in 24 hours.

If you did not request this password reset, please ignore this email or contact support.

This is an automated message from the VIMS system.
"""
    
    # Retry mechanism for network issues
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"[EMAIL] Attempt {attempt}/{max_retries}: Sending password reset email for user {user.username}")
            logger.info(f"[EMAIL] From: {from_email}, To: {recipient_email}")
            
            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=[recipient_email],
                fail_silently=False,
            )
            
            logger.info(f"[EMAIL] ✓ Password reset email sent successfully to {recipient_email} for user {user.username}")
            return True
            
        except Exception as e:
            logger.warning(f"[EMAIL] Attempt {attempt}/{max_retries} failed: {str(e)}")
            if attempt < max_retries:
                wait_time = attempt * 2  # Exponential backoff: 2s, 4s, 6s
                logger.info(f"[EMAIL] Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.error(f"[EMAIL] ✗ Failed to send email after {max_retries} attempts: {str(e)}", exc_info=True)
                # Don't raise exception - email failure shouldn't block password reset request
                return False
    
    return False
