# HoosHungry
## What is HoosHungry?
HoosHungry is a website where users can share, review, and find restaurants in the area on and around UVA Grounds! Visit our website  [hosted on heroku](https://hoos-hungry-9d841b5b9916.herokuapp.com/)

## Pages
### Restaurants
This page is where you can find and browse restaurants! The search bar will filter the restaurant list, and you can click on the restaurant cards to see where that restaurant is on the map.

### Make a Request
On this page, you can request to add a new restaurant to the website, or request to change the existing information about a restaurant. Requests you submit here are only requests, so they will not go through until an admin approves them.

### Write a Review
This is where you can write a review about your favorite (or least favorite) restaurant! Simply select the restaurant of choice, enter a review, enter a rating, and submit! Your review will be shown on the restaurant's page.

### Leave a Report
This is where you can leave quick stats about specific restaurant qualities, including cleanliness, crowdedness, friendliness, and menu quality. Although your individual report will not be displayed, it will be contribute to the average report rating of that restaurant.

## Admins
HoosHungry has admin functionality where normal users can request changes to a restaurant's information, and that restaurants admin can approve that request. One thing to keep in mind is that there are different admin roles for each restaurant. Additionally, there is a seperate admin role for the approval of new restaurant requests. This means that you may be admin for OHill, but that does not mean you will be an admin for Runk, or be able to approve new restaurant requests.

## Development
This webapp was developed in the fall of 2023 for a project in UVA's CS 3240, Advanced Software Development. It was built in collaboration with Rachit Goli, Eric Hamilton, Andrew Ma, and Connor Ware.

_To run this project on your machine:_
1. clone the project locally
2. run `python3 -m venv env; source env/bin/activate` to setup and use a virtual environment
4. run `pip install -r requirements.txt` to install the required dependencies
5. run `python manage.py runserver` to begin the webserver
