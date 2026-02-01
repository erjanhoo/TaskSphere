import os
from django.conf import settings
from django.http import FileResponse, Http404
from django.utils._os import safe_join


class ServeMediaMiddleware:
    """
    Middleware to serve media files in production when using Gunicorn.
    Only use this if you can't use a proper CDN or object storage.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only handle media URLs
        if request.path.startswith(settings.MEDIA_URL):
            # Get the file path relative to MEDIA_ROOT
            relative_path = request.path[len(settings.MEDIA_URL):]
            file_path = safe_join(str(settings.MEDIA_ROOT), relative_path)
            
            # Check if file exists
            if os.path.isfile(file_path):
                return FileResponse(open(file_path, 'rb'))
            else:
                raise Http404("Media file not found")
        
        # For all other requests, continue normally
        return self.get_response(request)
