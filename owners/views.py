from django.http import JsonResponse
from django.shortcuts import render, HttpResponse
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from . models import Owner, CarRegisteration, Approved_Centres
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from . forms import LoginForm, ALPRUploadForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from .alpr import ALPRService






@login_required
def user_login(request):
    """ user login view """
    if request.method == 'POST':
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


def logged_out(request):
    """Shown after a successful logout."""
    return render(request, 'registration/logged_out.html')


@login_required
def dashboard(request):
    context = {
        'total_owners': Owner.objects.count(),
        'total_vehicles': CarRegisteration.objects.count(),
        'total_centres': Approved_Centres.objects.count(),
        'recent_vehicles': CarRegisteration.objects.select_related('owner').order_by('-created')[:5],
        'recent_owners': Owner.objects.order_by('-created')[:5],
    }
    return render(request, 'content/dashboard.html', context)


@login_required
def alpr_upload(request):
    ocr_available = ALPRService._ocr_available()
    if request.method == 'POST':
        form = ALPRUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = form.cleaned_data['image']
            model_name = form.cleaned_data['model_name']
            result = ALPRService.process_upload(uploaded_file, model_name)
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'result': result})
            return render(request, 'content/alpr_result.html', {'result': result, 'form': form})
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'errors': form.errors})
    else:
        form = ALPRUploadForm()

    return render(request, 'content/alpr_upload.html', {
        'form': form,
        'models': ALPRService.get_available_models(),
        'ocr_available': ocr_available,
    })


# Search plate numbers
@login_required
def search(request):
    q = request.GET.get('q', '')
    cars = CarRegisteration.objects.filter(plate_number__icontains=q) if q else CarRegisteration.objects.none()

    return render(request, 'content/search.html', {
        'cars': cars,
        'data': cars,
        'query': q,
    })

# Search users/owners
@login_required
def searchUser(request):
    query = request.GET.get('query', '')
    users = Owner.objects.filter(full_name__icontains=query) if query else Owner.objects.none()
    return render(request, 'content/search_owner.html', {
        'users': users,
        'user_data': users,
        'query': query,
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
class OwnerRegistrationsDisplayViews(LoginRequiredMixin, DetailView):
    model = Owner
    context_object_name = "owner"
    template_name = "content/owner_detail.html"




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
    context_object_name = "form"
    success_url = reverse_lazy("dashboard")
    success_message = "Vehicle record updated successfully"
    template_name = "content/car_update.html"


# Car Registration Detail Views
class CarRegistrationDetailViews(LoginRequiredMixin, DetailView):
    model = CarRegisteration
    context_object_name = "car"
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



