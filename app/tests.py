from django.forms import ValidationError
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from app.models import *


class RestaurantMenuTestCase(TestCase):
    def setUp(self):
        pass

    def test_create_restaurant(self):
        restaurant = Restaurant.objects.create(
            name='Test Restaurant',
            address='123 Test St',
            latitude=12.34,
            longitude=-56.78,
            contact_info='123-456-7890'
        )
        self.assertEqual(restaurant.name, 'Test Restaurant')
        self.assertEqual(restaurant.address, '123 Test St')
        self.assertEqual(restaurant.latitude, 12.34)
        self.assertEqual(restaurant.longitude, -56.78)
        self.assertEqual(restaurant.contact_info, '123-456-7890')

    def test_invalid_latitude_longitude(self):
        with self.assertRaises(ValidationError):
            Restaurant.objects.create(
                name='Invalid Restaurant',
                address='456 Test Ave',
                latitude=100.0,  # Invalid latitude
                longitude=-74.0060,
                contact_info='123-456-7890'
            )
        with self.assertRaises(ValidationError):
            Restaurant.objects.create(
                name='Invalid Restaurant',
                address='456 Test Ave',
                latitude=40.7128,
                longitude=-200.0,  # Invalid longitude
                contact_info='123-456-7890'
            )


class RestaurantRequestTestCase(TestCase):
    def setUp(self):
        self.restaurant = Restaurant.objects.create(
            name="ExistingRestaurant",
            address="ExistingAddress",
            latitude=50.0000,
            longitude=-65.0000,
            contact_info="2222222222"
        )
        self.restaurant_request = RestaurantRequest.objects.create(
            corresponding_restaurant=self.restaurant,
            name="RequestedRestaurant",
            address="RequestedAddress",
            latitude=40.0000,
            longitude=-75.0000,
            contact_info="1111111111"
        )
    
    def test_restaurant_request_approval(self):
        self.restaurant_request.approve()
        approved_restaurant = Restaurant.objects.get(name="RequestedRestaurant")
        self.assertIsInstance(approved_restaurant, Restaurant)
        with self.assertRaises(RestaurantRequest.DoesNotExist):
            RestaurantRequest.objects.get(name="RequestedRestaurant")


class ReviewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(email='test_user@email.com')
        self.restaurant = Restaurant.objects.create(
            name='Test Restaurant',
            address='Test Address',
            latitude=40.0000,
            longitude=-75.0000,
            contact_info='1111111111'
        )
        self.review = Review.objects.create(
            user=self.user,
            restaurant=self.restaurant,
            rating=5,
            review_text='Excellent!'
        )

    def test_review_creation(self):
        self.assertEqual(str(self.review), f"{self.user} rated {self.restaurant} 5/5\nExcellent!...")
        self.assertIn(self.review, self.user.reviews.all())
        self.assertIn(self.review, self.restaurant.reviews.all())
        
    def test_average_reviews(self):
        self.assertEqual(self.restaurant.get_average_rating(), 5)
        Review.objects.create(
            user=self.user,
            restaurant=self.restaurant,
            rating=1,
            review_text='Terrible!'
        )
        self.assertEqual(self.restaurant.get_average_rating(), 3)
        self.review.delete()
        self.assertEqual(self.restaurant.get_average_rating(), 1)


class ReportTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(email='test_user@email.com')
        self.restaurant = Restaurant.objects.create(
            name='Test Restaurant',
            address='Test Address',
            latitude=40.0000,
            longitude=-75.0000,
            contact_info='1111111111'
        )
        self.report = Report.objects.create(
            user=self.user,
            restaurant=self.restaurant,
            rating=5,
            report_type=Report.ReportType.CLEANLINESS,
        )

    def test_invalid_report(self):
        with self.assertRaises(TypeError):
            Report.objects.create(
                user=self.user,
                restaurant=self.restaurant,
                rating=1,
                report_type=Report.ReportType.CLEANLINESS,
                review_text='This report should not have a review text'
            )

    def test_average_reports(self):
        self.assertEqual(self.restaurant.get_average_cleanliness(), 5)
        Report.objects.create(
            user=self.user,
            restaurant=self.restaurant,
            rating=1,
            report_type=Report.ReportType.CLEANLINESS,
        )
        self.assertEqual(self.restaurant.get_average_cleanliness(), 3)
        self.report.delete()
        self.assertEqual(self.restaurant.get_average_cleanliness(), 1)


class ReadMessagesTests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(email='test@example.com', password='test')
        self.client = Client()
        RejectionMessage.objects.create(recipient=self.user, message="Message 1", read=False)
        RejectionMessage.objects.create(recipient=self.user, message="Message 2", read=False)
        RejectionMessage.objects.create(recipient=self.user, message="Message 3", read=True)

    def test_read_messages(self):
        self.client.login(email='test@example.com', password='test')

        # Send POST request to the endpoint
        response = self.client.post(reverse('app:read_messages'))

        # Make sure the user is redirected
        self.assertEqual(response.status_code, 302)

        # Verify that all messages are now read
        messages = RejectionMessage.objects.filter(recipient=self.user)
        self.assertTrue(all(message.read for message in messages))
