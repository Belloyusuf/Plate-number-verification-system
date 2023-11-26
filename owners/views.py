from django.shortcuts import render
from django.views.generic.edit import ListView, CreateView, UpdateView
from . models import Owner, CarRegisteration
from django.contrib.messages.views import SuccessMessageMixin


# Create your views here.

def dashboard(request):
    return render(request, 'content/dashboard.html')


class OwnerRegistrationViews(SuccessMessageMixin, CreateView):
    model = Owner
    fields = "__all__"
    context_object_name = "owners"
    success_url = "/dashboard/"
    success_message = "%(full_name)s was created successfully"
    template_name = "content/create.html"
    

