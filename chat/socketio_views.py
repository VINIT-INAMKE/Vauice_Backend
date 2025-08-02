"""
Socket.io integration via Django views
This approach keeps Socket.io separate from the main WSGI app
"""

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import socketio
from .socketio_complete import sio

# Create a standalone Socket.io WSGI app for the endpoint
socketio_app = socketio.WSGIApp(sio, static_files={})

@csrf_exempt
def socketio_endpoint(request):
    """
    Handle Socket.io requests through Django view
    This keeps Socket.io isolated from other API calls
    """
    # Create a WSGI environ from Django request
    environ = request.META.copy()
    environ['REQUEST_METHOD'] = request.method
    environ['PATH_INFO'] = '/socket.io/' + request.path.split('/socket.io/')[-1]
    environ['QUERY_STRING'] = request.META.get('QUERY_STRING', '')
    environ['CONTENT_TYPE'] = request.META.get('CONTENT_TYPE', '')
    environ['CONTENT_LENGTH'] = request.META.get('CONTENT_LENGTH', '')
    
    # Handle the request with Socket.io
    def start_response(status, headers):
        # Convert Socket.io response to Django response
        response = HttpResponse()
        response.status_code = int(status.split()[0])
        for header_name, header_value in headers:
            response[header_name] = header_value
        return response
    
    try:
        result = socketio_app(environ, start_response)
        if result:
            content = b''.join(result)
            response = HttpResponse(content)
            return response
    except Exception as e:
        return HttpResponse(f"Socket.io error: {str(e)}", status=500)
    
    return HttpResponse("Socket.io endpoint", status=200)