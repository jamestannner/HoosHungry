from django.urls import path
from django.contrib.auth.views import LogoutView

from . import views 
from .views import ReportCreateView

app_name = "app"
urlpatterns = [
    path("", views.index, name="index"),
    path("logout", LogoutView.as_view(), name="logout"),
    path("restaurants", views.RestaurantListView.as_view(), name="restaurants"),
    path("restaurants/<int:pk>", views.RestaurantView.as_view(), name="restaurant_detail"),
    path("restaurants/<int:pk>/update", views.RestaurantUpdateView.as_view(), name="restaurant_update"),
    path('restaurant_request/<int:pk>/approve/', views.ApproveRequestView.as_view(), name='approve_request'),
    path('restaurant_request/<int:pk>/reject/', views.RejectRequestView.as_view(), name='reject_request'),
    path('restaurant_request/', views.restaurant_request_view, name='create_request'),
    path('restaurant_request/<int:restaurant_id>/', views.restaurant_request_view, name='create_request_filled'),
    path("reviews/<int:pk>", views.ReviewView.as_view(), name="review_detail"),
    # path("report_form", views.ReportFormView.as_view(), name="report_form"),
    path("review", views.ReviewFormView.as_view(), name="review_form"),
    path("restaurant_request/new", views.NewRestaurantView.as_view(), name="new_restaurant"),
    # path('reports/', ReportListView.as_view(), name='report_list'),
    path('reports/create/', ReportCreateView.as_view(), name='report_create'),
    path('read_messages/', views.read_messages, name='read_messages'),
]
