from django.contrib import admin

from .models import User, Restaurant, Review, Report, RestaurantRequest, RejectionMessage

admin.site.register(User)
admin.site.register(Restaurant)
admin.site.register(Review)
admin.site.register(Report)
admin.site.register(RestaurantRequest)
admin.site.register(RejectionMessage)
