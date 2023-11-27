from django.shortcuts import render
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from . models import Owner, CarRegisteration, Approved_Centres
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy

# Create your views here.

def dashboard(request):
    return render(request, 'content/dashboard.html')



def search(request):
    q = request.GET['q']
    plate_number = CarRegisteration.objects.filter(old_plate_number__contains=q)
    data = CarRegisteration.objects.filter(old_plate_number__contains=q)

    return render(request,   'content/search.html',{
        'plate_number':plate_number,
        'data':data
    })



#  List car owners
class OwnerRegistrationListViews(ListView):
    model = Owner
    paginate_by = 10
    context_object_name = "owners"
    template_name = "content/list.html"


#  Create views for car owners
class OwnerRegistrationViews(SuccessMessageMixin, CreateView):
    model = Owner
    fields = "__all__"
    context_object_name = "form"
    success_url = reverse_lazy("dashboard")
    success_message = "%(full_name)s was created successfully"
    template_name = "content/create.html"


# Update views for car owners
class OwnerRegistrationsUpdateViews(SuccessMessageMixin, UpdateView):
    model = Owner
    fields = "__all__"
    context_object_name = "form"
    success_url = reverse_lazy("dashboard")
    success_message = "%(full_name)s was updated successfully"
    template_name = "content/update.html"
    

# Display views for car owners
class OwnerRegistrationsDisplayViews(DetailView):
    model = Owner
    context_object_name = "owners"
    template_name = "content/detail.html"




# Car registration list views
class CarRegistrationListViews(ListView):
    model = CarRegisteration
    context_object_name = "cars"
    paginate_by = 10
    template_name = "content/car_list.html"


#  Car Registration create views
class CarRegistrationCreateView(SuccessMessageMixin, CreateView):
    model = CarRegisteration
    fields = "__all__"
    context_object_name = "form"
    success_url = reverse_lazy("dashboard")
    success_message = "%(vehicle_type)s was created successfully"
    template_name = "content/car_create.html"


# Car Registration Update Views
class CarRegistrationUpdateViews(SuccessMessageMixin, UpdateView):
    model = CarRegisteration
    fields = "__all__"
    context_object_name = "cars"
    success_url = reverse_lazy("dashboard")
    template_name = "content/car_update.html"


# Car Registration Detail Views
class CarRegistrationDetailViews(DetailView):
    model = CarRegisteration
    context_object_name = "cars"
    template_name = "content/car_detail.html"


#  Approve state list views
class ApproveListViews(ListView):
    model = Approved_Centres
    context_object_name = "states"
    template_name = "content/state.html"


# Approve state create views
class ApproveCreateViews(SuccessMessageMixin, CreateView):
    model = Approved_Centres
    fields = "__all__"
    template_name = "content/state_create.html"
    success_url = reverse_lazy("dashboard")
    success_message = "%(state)s was approved successfully"



