from django.urls import path
from . import views
from . views import OwnerRegistrationListViews, OwnerRegistrationsDisplayViews, OwnerRegistrationsUpdateViews, \
                    OwnerRegistrationViews, CarRegistrationCreateView, CarRegistrationDetailViews, \
                    CarRegistrationUpdateViews, CarRegistrationListViews

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
]
