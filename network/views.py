import json
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import HttpResponse, HttpResponseRedirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator

from .models import *


def index(request):

    # Index page redirects to the homepage
    return HttpResponseRedirect(reverse("home"))


def home(request):
    
    # Render the homepage
    return render(request, "network/index.html", {"view": "home"})


def profile(request, username):

    # Query for the user with provided username
    try:
        user= User.objects.get(username=username)
        
    except User.DoesNotExist:

        # Render Not Found view
        return render(request, "network/index.html", {"view": "notFound"})

    # Render the profile Page of some user
    return render(request, "network/index.html", {"view": "profile", "profile_owner": username})


@login_required
def following(request):

    # Render the following Page of the authenticated user 
    return render(request, "network/index.html", {"view": "following"})


# API
@csrf_exempt
def compose(request):
    
    # Posting a new post must be via POST
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=400)

    # User must be authenticated
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized request."}, status=401)

    # Get the data
    data = json.loads(request.body)


    # Content must be provided 
    if data.get("content") is None:
        return JsonResponse({"error": "Content must be provided!"}, status=400)

    # Post must not be empty
    if data.get("content") == "":
        return JsonResponse({"error": "Post can't be empty!"}, status=400)

    # Create the post
    post = Post(
        publisher=request.user,
        content=data["content"]
    )

    post.save()
    return JsonResponse({"message": "Post created successfully."}, status=201)


@csrf_exempt
def edit(request, id):

    # Editing post must be via PUT
    if request.method != "PUT":
        return JsonResponse({"error": "PUT request required."}, status=400)

    # User must be authenticated
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized request."}, status=401)

    # Query for requested post
    try:
        post = Post.objects.get(pk=id)
    except Post.DoesNotExist:
        return JsonResponse({"error": "Post not found."}, status=404)

    # User must be the publisher
    if post.publisher != request.user: 
        return JsonResponse({"error": "Not authorized to edit this post"}, status=403)

    # Get the data
    data = json.loads(request.body)

    # Content must be provided 
    if data.get("content") is None:
        return JsonResponse({"error": "Content must be provided!"}, status=400)

    # Post must not be empty
    if data.get("content") == "":
        return JsonResponse({"error": "Post can't be empty!"}, status=400)

    post.content = data["content"]
    post.save()
    return JsonResponse({"message": "Post edited successfully"}, status=200)


@csrf_exempt
def like_toggle(request, id):

    # Like/Unlike must be via POST
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=400)

    # User must be authenticated
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized request."}, status=401)

    # Query for post and if user liked it or not
    try: 
        post = Post.objects.get(id=id)
        like = Like.objects.get(post=post, liked_by=request.user)

    except Post.DoesNotExist:
        return JsonResponse({"error": f"Post with id {id} does not exist."}, status=400)

    except Like.DoesNotExist:

        # Like
        like = Like(
            post=post,
            liked_by=request.user
        )

        like.save()
        return JsonResponse({"message": "Liked"}, status=200)

    # Unlike
    like.delete()
    return JsonResponse({"message": "Unliked"}, status=200)


def home_posts(request, page):

    # Get method requried
    if request.method != "GET":
        return JsonResponse({"error": "GET request required."}, status=400)

    # Query for all posts of the network
    posts = Post.objects.all()

    # Return posts of required page in reverse chronologial order + paginator data
    posts = posts.order_by("-timestamp").all()
    p = Paginator(posts, 10)
    pageX = p.page(page)

    return JsonResponse({
        "posts":[post.serialize(request.user) for post in pageX.object_list], 
        "paginator": {
            "numPages": p.num_pages, 
            "currPage": page, 
            "prev": pageX.has_previous(), 
            "next": pageX.has_next()
        }
    }, safe=False)


def following_posts(request, page):

    # GET method requried
    if request.method != "GET":
        return JsonResponse({"error": "GET request required."}, status=400)

    # User must be authenticated
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized request."}, status=401)

    # Get posts of publishers in user's following
    posts = Post.objects.filter(
        publisher__in=request.user.following.all()
    )

    # Return posts in reverse chronologial order
    posts = posts.order_by("-timestamp").all()
    p = Paginator(posts, 10)
    pageX = p.page(page)
    return JsonResponse({
        "posts":[post.serialize(request.user) for post in pageX.object_list], 
        "paginator": {
            "numPages": p.num_pages, 
            "currPage": page, 
            "prev": pageX.has_previous(), 
            "next": pageX.has_next()
        }
    }, safe=False)


def profile_info(request, username):

    # Query for the profile owner
    try:
        profile_owner = User.objects.get(username=username)
    except User.DoesNotExist:
        return JsonResponse({"error": f"User with username {username} does not exist."}, status=400)

    return JsonResponse(profile_owner.serialize(), safe=False)


@csrf_exempt
def follow_toggle(request, username):

    # Follow/Unfollow must be via POST
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=400)

    # User must be authenticated
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized request."}, status=401)

    # Users not allowed to follow them thelves
    if request.user.username == username:
        return JsonResponse({"error": "Users not allowed to follow themselves"})

    # Query for requested profile owner
    try:
        profile_owner = User.objects.get(username=username)
    except User.DoesNotExist:
        return JsonResponse({"error": "User to follow/unfollow not found."}, status=404)



    # Check if user is a follower of the profile owner
    follower = profile_owner.followers.filter(username=request.user).exists()
    
    if not follower:
        profile_owner.followers.add(request.user)

    if follower:
        profile_owner.followers.remove(request.user)

    profile_owner.save()

    return JsonResponse({"message": "Toggled follow/unfollow."}, status=201)


def in_Following(request, username):
    
    # GET method required
    if request.method != "GET":
        return JsonResponse({"error": "GET request required."}, status=400)

    # User must be authenticated
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized request."}, status=401)

    # Query for profile owner 
    try:
        profile_owner = User.objects.get(username=username)
    except User.DoesNotExist:
        return JsonResponse({"error": f"User with username {username} does not exist."}, status=400)

    # Return result
    result = request.user.following.filter(username=profile_owner.username).exists()
    return JsonResponse({"inFollowing": result}, safe=False) 


def profile_posts(request, username, page):
    
    # Get method requried
    if request.method != "GET":
        return JsonResponse({"error": "GET request required."}, status=400)

    # Get post of the profile owner
    posts = Post.objects.filter(
        publisher=User.objects.get(username=username)
    )

    # Return posts in reverse chronologial order
    posts = posts.order_by("-timestamp").all()
    p = Paginator(posts, 10)
    pageX = p.page(page)

    return JsonResponse({
        "posts":[post.serialize(request.user) for post in pageX.object_list],
        "paginator": {
            "numPages": p.num_pages,
            "currPage": page,
            "prev": pageX.has_previous(),
            "next": pageX.has_next()
            }
        }, safe=False)


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
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "network/login.html")


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
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")
