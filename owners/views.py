from django.shortcuts import render
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from . models import Owner, CarRegisteration
from django.contrib.messages.views import SuccessMessageMixin


# Create your views here.

def dashboard(request):
    return render(request, 'content/dashboard.html')



#  List car owners
class OwnerRegistrationListViews(ListView):
    model = Owner
    context_object_name = "owners"
    template_name = "content/list.html"


#  Create views for car owners
class OwnerRegistrationViews(SuccessMessageMixin, CreateView):
    model = Owner
    fields = "__all__"
    context_object_name = "form"
    success_url = "/dashboard/"
    success_message = "%(full_name)s was created successfully"
    template_name = "content/create.html"


# Update views for car owners
class OwnerRegistrationsUpdateViews(SuccessMessageMixin, UpdateView):
    model = Owner
    fields = "__all__"
    context_object_name = "form"
    success_url = "/dashboard/"
    success_message = "%(full_name)s was updated successfully"
    template_name = "content/update.html"
    

# Display views for car owners
class OwnerRegistrationsDisplayViews(DetailView):
    model = Owner
    context_object_name = "owners"
    template_name = "content/detail.html"




# Car registration list views
class CarRegistrationViews(ListView):
    model = CarRegisteration
    context_object_name = "cars"
    template_name = "content/car_list.html"


#  Car Registration create views
class CarRegistrationCreateView(SuccessMessageMixin, CreateView):
    model = CarRegisteration
    fields = "__all__"
    context_object_name = "form"
    success_url = "/dashboard/"
    success_message = "%(vehicle_type)s was created successfully"
    template_name = "content/car_create.html"


# Car Registration Update Views
class CarRegistrationUpdateViews(SuccessMessageMixin, UpdateView):
    model = CarRegisteration
    fields = "__all__"
    context_object_name = "cars"
    template_name = "content/car_update.html"



# Car Registration Detail Views
class CarRegistrationDetailViews(DetailView):
    model = 