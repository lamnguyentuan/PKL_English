from django.shortcuts import render, redirect

def login_page(request):
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'users/login.html')

def register_page(request):
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'users/register.html')