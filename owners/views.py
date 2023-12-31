from django.shortcuts import render, HttpResponse
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from . models import Owner, CarRegisteration, Approved_Centres
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from . forms import LoginForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login


@login_required
def user_login(request):
    """ user login view """
    if request.methond == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            user = authenticate(request,
                                username=cd['username'],
                                password=cd['password']
                            )
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return HttpResponse('Login sucessfully')
                else:
                    return HttpResponse('Disable')
            else:
                return HttpResponse('Invalid Account')
    else:
        form = LoginForm()
    return render(request, 'registration/login.html')


@login_required
def dashboard(request):
    return render(request, 'content/dashboard.html')


# Search plate numbers
@login_required
def search(request):
    q = request.GET['q']
    plate_number = CarRegisteration.objects.filter(old_plate_number__contains=q)
    data = CarRegisteration.objects.filter(old_plate_number__contains=q)

    return render(request,   'content/search.html',{
        'plate_number':plate_number,
        'data':data
    })

# Search users/owners
@login_required
def searchUser(request):
    query = request.GET['query']
    users = Owner.objects.filter(full_name__icontains=query)
    user_data = Owner.objects.filter(full_name__icontains=query)
    return render(request, 'content/search_owner.html', {
        'users':users,
        'user_data':user_data
    })



#  List car owners
class OwnerRegistrationListViews(LoginRequiredMixin, ListView):
    model = Owner
    paginate_by = 10
    context_object_name = "owners"
    template_name = "content/list.html"


#  Create views for car owners
class OwnerRegistrationViews(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Owner
    fields = "__all__"
    context_object_name = "form"
    success_url = reverse_lazy("dashboard")
    success_message = "%(full_name)s was created successfully"
    template_name = "content/create.html"


# Update views for car owners
class OwnerRegistrationsUpdateViews(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
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
class CarRegistrationListViews(LoginRequiredMixin, ListView):
    model = CarRegisteration
    context_object_name = "cars"
    paginate_by = 10
    template_name = "content/car_list.html"


#  Car Registration create views
class CarRegistrationCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = CarRegisteration
    fields = "__all__"
    context_object_name = "form"
    success_url = reverse_lazy("dashboard")
    success_message = "%(vehicle_type)s was created successfully"
    template_name = "content/car_create.html"


# Car Registration Update Views
class CarRegistrationUpdateViews(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
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
class ApproveListViews(LoginRequiredMixin, ListView):
    model = Approved_Centres
    context_object_name = "states"
    template_name = "content/state.html"


# Approve state create views
class ApproveCreateViews(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Approved_Centres
    fields = "__all__"
    template_name = "content/state_create.html"
    success_url = reverse_lazy("dashboard")
    success_message = "%(state)s was approved successfully"



