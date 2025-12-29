from django.shortcuts import redirect, render
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .forms import CustomUserCreationForm, ProfileUpdateForm

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            messages.success(request, f'Tài khoản {username} đã được tạo thành công!')
            return redirect('home')
        else:
            messages.error(request, "Đăng ký thất bại. Vui lòng kiểm tra lại thông tin.")
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})


@login_required
def profile_edit(request):
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Cập nhật thông tin thành công!")
            return redirect("profile_edit")
        else:
            messages.error(request, "Cập nhật thất bại. Vui lòng kiểm tra lại thông tin.")
    else:
        form = ProfileUpdateForm(instance=request.user)

    return render(request, "users/profile_edit.html", {"form": form})
