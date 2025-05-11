from django.http import HttpResponse
from django.template import loader
from django.utils.deprecation import MiddlewareMixin

class CustomErrorMiddleware(MiddlewareMixin):
    """
    Middleware to handle custom HTTP error responses
    """
    
    def process_response(self, request, response):
        """
        Process the response and return custom error pages for error status codes
        """
        # Only process error responses that don't already have content
        if 400 <= response.status_code < 600 and not response.content:
            # Define error titles and messages for common status codes
            error_details = {
                400: ('Bad Request', 'The request could not be processed due to invalid syntax.'),
                401: ('Authentication Required', 'You need to be logged in to access this page.'),
                403: ('Access Denied', 'You don\'t have permission to access this page.'),
                404: ('Page Not Found', 'The page you\'re looking for doesn\'t exist or has been moved.'),
                500: ('Server Error', 'Something went wrong on our end. Our team has been notified.'),
                502: ('Bad Gateway', 'The server received an invalid response from an upstream server.'),
                503: ('Service Unavailable', 'The server is temporarily unavailable. Please try again later.'),
                504: ('Gateway Timeout', 'The server timed out waiting for a response from an upstream server.')
            }
            
            # Get error details or use generic ones
            error_title, error_message = error_details.get(
                response.status_code, 
                (f'Error {response.status_code}', 'An error occurred. Please try again later.')
            )
            
            # Try to use a specific template for this status code, fall back to generic
            try:
                template = loader.get_template(f'errors/{response.status_code}.html')
            except:
                template = loader.get_template('errors/generic.html')
            
            # Render the template with context
            context = {
                'status_code': response.status_code,
                'error_title': error_title,
                'error_message': error_message
            }
            
            # Create a new response with the rendered template
            content = template.render(context, request)
            response = HttpResponse(content, status=response.status_code)
        
        return response
