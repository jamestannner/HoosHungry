# -*- coding: utf-8 -*-

import json
from typing import Any
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.template import loader
from .models import Review, Restaurant, RestaurantRequest, RejectionMessage
from django.http import Http404
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views import generic, View
from django.utils import timezone
from django.views.generic import UpdateView, ListView, CreateView
from django.forms import modelformset_factory
from django.shortcuts import redirect
from django.core.serializers import serialize
from .forms import RestaurantRequestForm, ReviewForm, ReportForm
from .models import Report


# Create your views here.


def index(request):
    # Convert QuerySet to list of dicts
    restaurants = Restaurant.objects.all()
    restaurant_list = [{
        'pk': restaurant.pk,
        'name': restaurant.name,
        'address': restaurant.address,
        'latitude': restaurant.latitude,
        'longitude': restaurant.longitude,
        'contact_info': restaurant.contact_info,
        'avg_rating': restaurant.get_average_rating(),
        'id': restaurant.id,
    } for restaurant in restaurants]
    
    restaurants_json = json.dumps(restaurant_list)

    if request.user.is_authenticated:
        messages = RejectionMessage.objects.filter(recipient=request.user, read=False)
    else:
        messages = []

    context = {
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
        'restaurants': restaurants_json,
        'messages': messages,
    }
    return render(request, "app/index.html", context=context)


class RestaurantListView(generic.ListView):
    template_name = "app/restaurantlist.html"
    context_object_name = "restaurant_list"

    def get_queryset(self):
        return Restaurant.objects.order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['google_maps_api_key'] = settings.GOOGLE_MAPS_API_KEY

        restaurant_list = [{
            'pk': restaurant.pk,
            'name': restaurant.name,
            'address': restaurant.address,
            'latitude': restaurant.latitude,
            'longitude': restaurant.longitude,
            'contact_info': restaurant.contact_info,
            'avg_rating': restaurant.get_average_rating(),
            'id': restaurant.id,
        } for restaurant in Restaurant.objects.all()]
        restaurants_json = json.dumps(restaurant_list)
        context['restaurants'] = restaurants_json

        is_admin = self.request.user.groups.filter(name="admin of everything").exists()
        context["is_admin"] = is_admin

        return context


class RestaurantView(generic.DetailView):
    template_name = "app/restaurant.html"
    model = Restaurant
    # display various aspects of restaurant info

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        is_admin = self.request.user.groups.filter(name=str(self.object.pk) + ' admin').exists()
        context["is_admin"] = is_admin
        return context


class RestaurantUpdateView(generic.DetailView):
    template_name = "app/restaurant_update.html"
    model = Restaurant

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        restaurant_requests = RestaurantRequest.objects.filter(corresponding_restaurant=self.object)
        context['restaurant_requests'] = restaurant_requests

        is_admin = self.request.user.groups.filter(name=str(self.object.pk) + ' admin').exists()
        context["is_admin"] = is_admin

        return context


class ApproveRequestView(View):
    def post(self, request, *args, **kwargs):
        request_id = kwargs.get('pk')
        restaurant_request = get_object_or_404(RestaurantRequest, pk=request_id)
        has_corr = restaurant_request.corresponding_restaurant is not None
        restaurant_request.approve()

        if has_corr:
            return HttpResponseRedirect(reverse('app:restaurant_update', args=[restaurant_request.corresponding_restaurant.pk]))

        return HttpResponseRedirect(reverse('app:new_restaurant'))


class RejectRequestView(View):
    def post(self, request, *args, **kwargs):
        request_id = kwargs.get('pk')
        restaurant_request = get_object_or_404(RestaurantRequest, pk=request_id)
        has_corr = restaurant_request.corresponding_restaurant is not None

        rejection_message = request.POST.get('rejection_message', '')
        if rejection_message == "":
            rejection_message = "No message provided."
        if restaurant_request.requester is not None:
            RejectionMessage.objects.create(
                recipient=restaurant_request.requester,
                for_what=restaurant_request.name,
                message=rejection_message,
                read=False
            )

        restaurant_request.delete()

        if has_corr:
            return HttpResponseRedirect(reverse('app:restaurant_update', args=[restaurant_request.corresponding_restaurant.pk]))

        return HttpResponseRedirect(reverse('app:new_restaurant'))


class ReviewView(generic.DetailView):
    template_name = "app/review.html"
    model = Review

class ReviewFormView(CreateView):
    template_name = "app/review_form.html"
    form_class = ReviewForm

    def form_valid(self, form):
        user = self.request.user

        if form.is_valid():
            review = Review(
                user=user,
                restaurant=form.cleaned_data['restaurant'],
                rating=form.cleaned_data['rating'],
                review_text=form.cleaned_data['review_text']
            )
            review.save()
            return redirect(reverse("app:review_form") + '?success=True')
        else:
            return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        context = super(ReviewFormView, self).get_context_data(**kwargs)
        success_message = self.request.GET.get('success', 'False') == 'True'
        context['success'] = success_message
        return context
    
def restaurant_request_view(request, restaurant_id=None):
    initial_data = {}

    if restaurant_id:
        restaurant = get_object_or_404(Restaurant, id=restaurant_id)
        initial_data['corresponding_restaurant'] = restaurant
        initial_data['name'] = restaurant.name
        initial_data['address'] = restaurant.address
        initial_data['latitude'] = restaurant.latitude
        initial_data['longitude'] = restaurant.longitude
        initial_data['contact_info'] = restaurant.contact_info
        initial_data['menu_text'] = restaurant.menu_text

    form = RestaurantRequestForm(initial=initial_data)

    if request.method == 'POST':
        form = RestaurantRequestForm(request.POST)
        if form.is_valid():
            rest_req = form.save(commit=False)
            if not request.user.is_anonymous:
                rest_req.requester = request.user
            rest_req.save()
            return redirect(reverse('app:create_request') + '?success=True')

    context = {'form': form}
    success_message = request.GET.get('success', 'False') == 'True'
    context['success'] = success_message

    return render(request, 'app/create_request.html', context)


class NewRestaurantView(generic.ListView):
    template_name = "app/new_restaurant.html"
    context_object_name = "new_restaurants_list"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        is_admin = self.request.user.groups.filter(name="admin of everything").exists()
        context["is_admin"] = is_admin

        return context

    def get_queryset(self):
        return RestaurantRequest.objects.filter(corresponding_restaurant=None)
    
# class ReportListView(View):
#     template_name = "app/report_list.html"
#     def get(self, request, *args, **kwargs):
#         reports = Report.objects.all()
#         context = {'reports': reports}
#         return render(request, self.template_name, context)

class ReportCreateView(View):
    template_name = 'app/report_create.html'

    def get(self, request, *args, **kwargs):
        form = ReportForm()
        success_message = request.GET.get('success', 'False') == 'True'
        context = {'form': form, 'success': success_message}
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = ReportForm(request.POST)  
        if form.is_valid():
            report = form.save(commit=False)
            report.user = request.user  
            report.save()
            return redirect(reverse('app:report_create') + '?success=True')
        else:
            context = {'form': form}
            return render(request, self.template_name, context)   


def read_messages(request):
    if request.method == 'POST':
        user = request.user
        RejectionMessage.objects.filter(recipient=user, read=False).update(read=True)
        return HttpResponseRedirect(reverse('app:index'))
