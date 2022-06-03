from django.contrib import admin
from .models import Hotel, HotelReview, HotelPrice
# Register your models here.


admin.site.register(Hotel)
admin.site.register(HotelPrice)

admin.site.register(HotelReview)
