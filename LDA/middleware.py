from django.shortcuts import redirect

class RedirectAuthenticatedUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and request.path == '/login/':
            return redirect('home')  # Ganti 'home' dengan nama view atau URL tujuan Anda
        if request.user.is_authenticated and request.path == '/register/':
            return redirect('home')  # Ganti 'home' dengan nama view atau URL tujuan Anda

        response = self.get_response(request)
        return response
