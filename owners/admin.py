from django.contrib import admin
from . models import Owner, CarRegisteration, Approved_Centres
# Register your models here.


admin.site.site_header = "Plate Number Verification System"
admin.site.site_title = "Car Plate Number Verification"

@admin.register(Owner)
class ownerAdmin(admin.ModelAdmin):
    list_display = ["full_name", "occupation", "created"]


@admin.register(CarRegisteration)
class CarRegisterationAdmin(admin.ModelAdmin):
    list_display = ["plate_number", "owner", "vehicle_type", "color", "created"]
    search_fields = ["plate_number", "owner__full_name"]


@admin.register(Approved_Centres)
class ApprovedCentresAdmin(admin.ModelAdmin):
    list_display = ["state", "location", "created"]

