from django.contrib import admin
from . models import Owner, CarRegisteration
# Register your models here.


admin.site.site_header = "Plate Number Verification System"
admin.site.site_title = "car plate number varification"

@admin.register(Owner)
class ownerAdmin(admin.ModelAdmin):
    list_display = ["full_name", "created"]




admin.site.register(CarRegisteration)

