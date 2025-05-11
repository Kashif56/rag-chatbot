# Email Verification with OTP

This document explains the email verification feature that has been added to the RAG Chatbot application.

## Overview

The email verification system uses a one-time password (OTP) sent to the user's email address to verify their identity. Users must verify their email before they can access the platform.

## Features

- OTP-based email verification
- Automatic redirection to verification page for unverified users
- Resend OTP functionality
- 10-minute expiration for OTP codes
- Middleware to enforce verification across the application

## How It Works

1. When a user signs up, an OTP code is generated and sent to their email
2. The user must enter this code on the verification page
3. Once verified, the user can access all features of the platform
4. If a user tries to log in without verifying their email, they will be redirected to the verification page

## Implementation Details

### New Models

- `UserProfile`: Extends the User model with verification fields
- `OTPVerification`: Stores OTP codes and their status

### New Views

- `verify_email`: Handles OTP verification
- `resend_otp`: Allows users to request a new OTP
- `verification_success`: Shown after successful verification

### Middleware

A middleware has been added to enforce email verification across the application. It redirects unverified users to the verification page when they try to access protected resources.

## Setup Instructions

1. Make sure to add the following environment variables for email configuration:

```
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@nexusai.com
```

2. Run migrations to create the new database tables:

```
python manage.py makemigrations accounts
python manage.py migrate
```

3. Restart your application

## Notes for Gmail Users

If you're using Gmail as your email provider, you'll need to:

1. Enable 2-factor authentication on your Google account
2. Generate an "App Password" specifically for this application
3. Use that App Password in the `EMAIL_HOST_PASSWORD` environment variable

## Testing the Feature

1. Register a new user
2. Check the email for the OTP code
3. Enter the code on the verification page
4. After verification, you should be able to access the platform

## Troubleshooting

- If emails are not being sent, check your email configuration in the environment variables
- If users are being redirected to verification page after verifying, check that the `is_email_verified` flag is being set correctly
- For local development, you can use Django's console email backend by setting `EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'` in settings.py
