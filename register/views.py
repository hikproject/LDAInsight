from django.shortcuts import render,redirect
from .form import RegisterForm,UbahPasswordForm
# Create your views here.
def register(response):
    if response.method == "POST":
        form = RegisterForm(response.POST)
        if form.is_valid():
            form.save() 
            return redirect("/")
    else:
        form = RegisterForm()
    return render(response,"registrasi/register.html",{"form":form})

def ubah_password(response):
    if response.method == "POST":
        form = UbahPasswordForm(response.user, response.POST)
        if form.is_valid():
            form.save() 
            return redirect("/")
    else:
        form = UbahPasswordForm(response.user)
    return render(response, "registrasi/ubahpassword.html", {"form": form})
