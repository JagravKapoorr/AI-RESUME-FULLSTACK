from django.shortcuts import render,HttpResponse,redirect
from .models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required


# Create your views here.
def home_view(request):
    return render(request, "accounts/home.html")

def register_view(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        role = request.POST.get("role")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered")
            return render(request, "accounts/register.html")

        User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=role,
        )

        messages.success(request, "Account created successfully")
        return redirect("accounts:login")

    return render(request, "accounts/register.html")


def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user) 
            return redirect("accounts:dashboard")
        else:
            messages.error(request, "Invalid email or password")

    return render(request, "accounts/login.html")

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully")
    return redirect("accounts:home")

@login_required
def dashboard(request):
    context = {
        'user': request.user,
    }
    return render(request, 'accounts/dashboard.html', context)
