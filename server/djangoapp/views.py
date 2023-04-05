from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from .models import CarMake, CarModel
from .restapis import get_dealers_from_cf, get_request, get_dealer_reviews_from_cf, get_dealer_by_id, get_dealers_by_state, post_request
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from datetime import datetime
import logging
import json

# Get an instance of a logger
logger = logging.getLogger(__name__)


# Create your views here.
def sample_django_vw(request):
    context = {}
    # If the request method is GET
    if request.method == 'GET':
        # Using the objects model manage to read all course list
        # and sort them by total_enrollment descending
        #course_list = Course.objects.order_by('-total_enrollment')[:10]
        # Appen the course list as an entry of context dict
        context['sample_text'] = 'Sample view and template'
        return render(request, 'djangoapp/static_django_template.html', context)


# Create an `about` view to render a static about page
def about(request):
    if request.method == 'GET':
        return render(request,'djangoapp/about.html')



# Create a `contact` view to return a static contact page
def contact(request):
    if request.method == 'GET':
        return render(request,'djangoapp/contact.html')

# Create a `login_request` view to handle sign in request
def login_request(request):
    context = {}
    # Handles POST request
    if request.method == "POST":
        # Get username and password from request.POST dictionary
        username = request.POST['username']
        password = request.POST['psw']
        # Try to check if provide credential can be authenticated
        user = authenticate(username=username, password=password)
        if user is not None:
            # If user is valid, call login method to login current user
            login(request, user)
            return redirect('djangoapp:index')
        else:
            #If not, return to login page again
            return render(request, 'djangoapp/user_login.html', context)            
    else:
        return render(request, 'djangoapp/user_login.html', context)


# Create a `logout_request` view to handle sign out request
def logout_request(request):
    # Get the user object based on session id in request
    print("Log out the user `{}`".format(request.user.username))
    # Logout user in the request
    logout(request)
    # Redirect user back to course list view
    return redirect('djangoapp:index')

# Create a `registration_request` view to handle sign up request
def registration_request(request):
    context = {}
    # If it is a GET request, just render the registration page
    if request.method == 'GET':
        return render(request, 'djangoapp/registration.html', context)
    # If it is a POST request
    elif request.method == 'POST':
        # Get user information from request.POST
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            # Check if user already exists
            User.objects.get(username=username)
            user_exist = True
        except:
            # If not, simply log this is a new user
            logger.debug("{} is new user".format(username))
        # If it is a new user
        if not user_exist:
            # Create user in auth_user table
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            # Login the user and redirect to course list page
            login(request, user)
            return redirect("djangoapp:index")
        else:
            return render(request, 'djangoapp/registration.html', context)

# Update the `get_dealerships` view to render the index page with a list of dealerships
def get_dealerships(request):
    context = {}
    if request.method == "GET":
        # url = "https://us-south.functions.cloud.ibm.com/api/dealerships/dealer-get" # give correct url
        url= "https://us-south.functions.appdomain.cloud/api/v1/web/49a1a341-7f80-4e2f-b9bc-2cfa6c0bcf63/dealership-package/get-dealership"
        # Get dealers from the URL
        # dealerships = get_dealers_from_cf(url)
        # Concat all dealer's short name
        # dealer_names = ' '.join([dealer.short_name for dealer in dealerships])
        # Return a list of dealer short name
        # return HttpResponse(dealer_names)
        context["dealerships"] = get_dealers_from_cf(url)
        return render(request, 'djangoapp/index.html', context)


# Create a `get_dealer_details` view to render the reviews of a dealer
# def get_dealer_details(request, dealer_id):
# ...
def get_dealer_details(request, dealer_id):
    context = {}
    if request.method == "GET":
        url = 'https://us-south.functions.appdomain.cloud/api/v1/web/49a1a341-7f80-4e2f-b9bc-2cfa6c0bcf63/dealership-package/get-review'
        reviews = get_dealer_reviews_from_cf(url, dealer_id=dealer_id)
        dealer_name = get_dealer_by_id('https://us-south.functions.appdomain.cloud/api/v1/web/49a1a341-7f80-4e2f-b9bc-2cfa6c0bcf63/dealership-package/get-dealership', dealer_id=dealer_id)
        context = {
            "reviews":  reviews, 
            "dealer_id": dealer_id,
            "dealer"   : dealer_name
        }

        return render(request, 'djangoapp/dealer_details.html', context)


# Create a `add_review` view to submit a review
# def add_review(request, dealer_id):
# ...
def add_review(request, dealer_id):
    # User must be logged in before posting a review
    if request.user.is_authenticated:
        # GET request renders the page with the form for filling out a review
        if request.method == "GET":
            url = f"https://us-south.functions.appdomain.cloud/api/v1/web/49a1a341-7f80-4e2f-b9bc-2cfa6c0bcf63/dealership-package/get-dealership?dealerId={dealer_id}"
            # Get dealer details from the API
            context = {
                "cars": CarModel.objects.all(),
                "dealer": get_dealer_by_id(url, dealer_id=dealer_id),
            }
            return render(request, 'djangoapp/add_review.html', context)

        # POST request posts the content in the review submission form to the Cloudant DB using the post_review Cloud Function
        # review_in = {"review": {"id": 1114,
    #           "name": "Navneet",
    #           "dealership": 15,
    #           "review": "My review",
    #           "purchase": 1,
    #           "purchase_date": "07/11/2020",
    #           "car_make": "Audi",
    #           "car_model": "A6",
    #           "car_year": 2010}}
        if request.method == "POST":
            form = request.POST
            review = dict()
            review["name"] = f"{request.user.username}"
            review["dealership"] = dealer_id
            review["review"] = form["content"]
            if form.get("purchasecheck") =='on':
                review["purchase"] = True
            if review["purchase"]:
                dt = datetime.strptime(form.get("purchasedate"), "%m/%d/%Y").isoformat()
                review["purchase_date"] = json.dumps(dt, default=str)
            car = CarModel.objects.get(pk=form["car"])
            review["car_make"] = car.car_make.name
            review["car_model"] = car.name
            review["car_year"] = car.model_year
            
            # If the user bought the car, get the purchase date
            if form.get("purchasecheck"):
                review["purchase_date"] = datetime.strptime(form.get("purchasedate"), "%m/%d/%Y").isoformat()
            else: 
                review["purchase_date"] = None

            # print('review payload is ' , review)
            url = "https://us-south.functions.appdomain.cloud/api/v1/web/49a1a341-7f80-4e2f-b9bc-2cfa6c0bcf63/dealership-package/post-review"  # API Cloud Function route
            json_payload = {"review": review}  # Create a JSON payload that contains the review data
            # Convert date object to string representation
            json_payload['review']['car_year'] = str(json_payload['review']['car_year'])
            print('json_payload payload is ' , json_payload)


            # Performing a POST request with the review
            result = post_request(url, json_payload, dealerId=dealer_id)
            print('result is ', result)
            if int(result.status_code) == 200:
                print("Review posted successfully.")

            # After posting the review the user is redirected back to the dealer details page
            return redirect("djangoapp:dealer_details", dealer_id=dealer_id)
            # return HttpResponseRedirect(reverse(viewname='djangoapp:dealer_details',dealer_id=dealer_id))

    else:
        # If user isn't logged in, redirect to login page
        print("User must be authenticated before posting a review. Please log in.")
        return redirect("/djangoapp/login")

