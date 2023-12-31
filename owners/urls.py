from django.urls import path
from . import views
from . views import OwnerRegistrationListViews, OwnerRegistrationsDisplayViews, OwnerRegistrationsUpdateViews, \
                    OwnerRegistrationViews, CarRegistrationCreateView, CarRegistrationDetailViews, \
                    CarRegistrationUpdateViews, CarRegistrationListViews, ApproveCreateViews, ApproveListViews

urlpatterns = [
    # Owner urls
    path("", views.dashboard, name="dashboard"),
    path("owner-list/", OwnerRegistrationListViews.as_view(), name="owner-list"),
    path("owner-create/", OwnerRegistrationViews.as_view(), name="owner-create"),
    path("owner-update/<int:pk>/owner/", OwnerRegistrationsUpdateViews.as_view(), name="owner-update"),
    path("owner-detail/<int:pk>/owner/", OwnerRegistrationsDisplayViews.as_view(), name="owner-detail"),
    # Car details urls
    path("car-list/", CarRegistrationListViews.as_view(), name="car-list"),
    path("car-create/", CarRegistrationCreateView.as_view(), name="car-create"),
    path("car-update/", CarRegistrationUpdateViews.as_view(), name="car-update"),
    path("car-detail/", CarRegistrationDetailViews.as_view(), name=""),
    # Approve State
    path("approve-state-create/", ApproveCreateViews.as_view(), name="state-create"),
    path("approve-state-list/", ApproveListViews.as_view(), name="state-list"),
    # Searching by plate number
    path("search", views.search, name="search"),
    # Search user/Owner
    path("search/owner", views.searchUser, name="searchUser"),
]
