from django.urls import path

from . import views


app_name = "accounts"

urlpatterns = [
    path("signup/", views.signup, name="signup"),
    path("login/", views.login_page, name="login"),
    path("logout/", views.logout_page, name="logout"),
    path("verify-email/", views.verify_email, name="verify_email"),
    path("resend-otp/", views.resend_otp, name="resend_otp"),
    path("verification-success/", views.verification_success, name="verification_success"),
]