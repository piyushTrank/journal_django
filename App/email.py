from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

def send_otp_email(email, otp):
    subject = "Journal A.I - Password Reset OTP"
    template_path = 'send-otp.html'
    print("===>",otp)
    try:
        message = render_to_string(template_path, {'otp': otp })
        msg = EmailMultiAlternatives(subject, '', settings.EMAIL_HOST_USER, [email])
        msg.attach_alternative(message, "text/html")
        msg.send()
    except Exception as e:
        print("Error: unable to send email:", e)
        return False
    return True