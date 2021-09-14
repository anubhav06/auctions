from typing import List, Type
from django.contrib.auth import authenticate, login, logout
from django.core.checks import messages
from django.db import IntegrityError
from django.db.models import query
from django.db.models.fields.related import ForeignKey
from django.http import HttpResponse, HttpResponseRedirect, request
from django.http.response import HttpResponseBadRequest, HttpResponseNotFound
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth.decorators import login_required

from .models import User, Listings, Bids, Comments, Watchlist
from .extras import List

def index(request):
    if request.method == "POST":

        if "title" in request.POST:
            #add listing
            #list=[
            #    "Fashion",
            #    "Toys",
            #    "Electronics",
            #    "Home",
            #    "Other"
            #]
            list = List.list

            if request.POST["list"] in list:
                if request.POST["title"] is None or request.POST["description"] is None or request.POST["price"] is None or request.POST["image"] is None or request.POST["list"] is None:
                    print(request.POST["title"])
                    print(request.POST["description"])
                    print(request.POST["price"])
                    print(request.POST["image"])
                    print(request.POST["list"])
                    return HttpResponseNotFound('<h1> All the fields are required to be filled </h1>')
                else:
                    entry = Listings(user=request.user, title = request.POST["title"], description = request.POST["description"], price = request.POST["price"], photo = request.POST["image"], category = request.POST["list"])
                    entry.save()
            else:
                return HttpResponseNotFound('<h1> The Category does not exist </h1>')

        elif "watchlistBtn" in request.POST: 
            #add to watchlist   

            # Gets the last value of the last url visited i.e. gets the listing id
            listingId = request.META.get('HTTP_REFERER').rsplit('/', 1)[-1]
            listing = Listings.objects.get(id=listingId)
            
            try:
                user = Watchlist.objects.get(watchlister=request.user ,listing=listing)
            except Watchlist.DoesNotExist:
                user = None
            
            if user is None:
                entry = Watchlist(watchlister=request.user, listing=listing)
                entry.save()
            else:
                user.delete()

        elif "submitBtn" in request.POST:
            # to bid
            bid = request.POST["bid"]
            listingId = request.META.get('HTTP_REFERER').rsplit('/', 1)[-1]
            listing = Listings.objects.get(id=listingId)
    
            
            try:
                # Get all the rows of Bids Model for the current listing id
                bidderListing = Bids.objects.filter(listing=listing)
            except Bids.DoesNotExist:
                bidderListing = None
            
            # Check that input value is greater than previous bid
            if bidderListing.exists():
                if int(bid) <= bidderListing.order_by("quote").last().quote :
                    return HttpResponseNotFound('<h1> Incorrect amount of bid entered! </h1>')


            # Add the new bid details to Bid Model
            entry = Bids(quote=bid, bidder=request.user, listing=listing)
            entry.save()
            # Update the listing price
            Listings.objects.filter(id=listingId).update(price=bid)


        elif "closeBtn" in request.POST:
            # to make the bidding inactive
            listingId = request.META.get('HTTP_REFERER').rsplit('/', 1)[-1]
            Listings.objects.filter(id=listingId).update(active=False)


        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/index.html", {
            #"listings" : Listings.objects.all()
            "listings" : Listings.objects.filter(active=True),
            "inactives" : Listings.objects.filter(active=False)
        })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")


@login_required(login_url='/login')
def listing(request, listing_id):
    
    if request.method == "POST":
        # If the comment form is submitted  
        comment = request.POST["comment"]
        listing = Listings.objects.get(id=listing_id)

        entry = Comments(comment=comment, commenter=request.user, auction=listing)
        entry.save()

        return HttpResponseRedirect(reverse("listing", args=(listing_id,)))

    else:

        listing = Listings.objects.get(id=listing_id)

        try:
            user = Watchlist.objects.get(listing=listing, watchlister=request.user)
        except Watchlist.DoesNotExist:
            user = None

        try:
            # Get all the rows of Bids Model for the current listing id
            bidderListing = Bids.objects.filter(listing=listing)
        except Bids.DoesNotExist:
            bidderListing = None
        
        # If bidding exists for the current listing:
        if bidderListing.exists():

            # Get the last object in the QuerySet for the latest(largest) bid
            quote = bidderListing.last().quote
            # Get the last bidder user which is the winner of the bid
            winner = bidderListing.last().bidder
            # Get the total count of objects in the QuerySet
            count = bidderListing.count()

        else:
            # If no bidding exists set the price to display as the initial bidding amount and set count as 0
            quote = listing.price
            winner = None
            count = 0

        if user is None:
            message = "Add to Watchlist"
        else:
            message = "Remove from Watchlist"

        comments = Comments.objects.filter(auction=listing)

        return render(request, "auctions/listing.html", {
            "listing": listing,
            "message": message,
            "quote": quote,
            "count": count,
            "winner": winner,
            "comments": comments
        })



@login_required(login_url='/login')
def watchlist(request):

    user = Watchlist.objects.filter(watchlister=request.user)
    watchlists = Listings.objects.filter(id__in = user.values_list('listing'))

    return render(request, "auctions/watchlist.html", {
        "watchlists" : watchlists
    })

def categories(request):
    # Get the category list from extras.py file
    categories = List.list

    return render(request, "auctions/categories.html", {
        "categories" : categories
    })

def category(request, category_name):

    # Get the listing details for the category_name
    listings = Listings.objects.filter(category = category_name)
    return render(request, "auctions/category.html", {
        "category_name" : category_name,
        "listings" : listings
    })


@login_required(login_url='/login')
def createListing(request):
    return render(request, "auctions/createListing.html")
