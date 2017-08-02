# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.shortcuts import render,redirect,render_to_response
from forms import SignUpForm,LoginForm,PostForm,LikeForm,CommentForm
from models import UserModel,SessionToken,PostModel,LikeModel,CommentModel
from django.contrib.auth.hashers import make_password,check_password
from imgurpython import ImgurClient
from instagram.settings import BASE_DIR

from datetime import timedelta

# Create your views here.
def signup_view(request):
    if request.method=='POST':
        form = SignUpForm(request.POST)
        print 'Post called'
        if form.is_valid():
            username=form.cleaned_data['username']
            name=form.cleaned_data['name']
            email=form.cleaned_data['email']
            password=form.cleaned_data['password']
            user=UserModel(name=name,password=make_password(password),email=email,username=username)
            user.save()
            return render(request,'success.html')
        else:
            print 'Invalid'
    elif request.method=='GET':
        form=SignUpForm()
    #today=datetime.now()
    return render(request,'signup.html',{'form':form})

def login_view(request):
    response_data={}
    if request.method=='POST':
        form=LoginForm(request.POST)
        if form.is_valid():
            username=form.cleaned_data.get('username')
            password=form.cleaned_data.get('password')
            user=UserModel.objects.filter(username=username).first()
            if user:
                if check_password(password,user.password):
                    token=SessionToken(user=user)
                    token.create_token()
                    token.save()
                    response=redirect('/feed/')
                    response.set_cookie(key='session_token',value=token.session_token)
                    return response
                    #return render(request,'feed.html',{'form': form})
                else:
                    #response_data['message'] = 'Incorrect Password! Please try it again.'
                    #print 'Incorrect Password! Please try it again.'
                    return render(request,'error.html')
    elif request.method=='GET':
        form=LoginForm()
    response_data['form']=form
    return render(request,'login.html',{'form': form})

def feed_view(request):
    user=check_validation(request)
    if user:
        posts=PostModel.objects.all().order_by('created_on')
        for post in posts:
            existing_like=LikeModel.objects.filter(post_id=post.id, user=user).first()
            if existing_like:
                post.has_liked=True
        return render(request, 'feed.html', {'posts':posts} )
    else:
        return redirect('/login/')

def check_validation(request):
    if request.COOKIES.get('session_token'):
        session=SessionToken.objects.filter(session_token=request.COOKIES.get('session_token')).first()
        if session:
            return session.user
        else:
            return None

def post_view(request):
    user=check_validation(request)
    if user:
        if request.method=="POST":
            form=PostForm(request.POST, request.FILES)
            if form.is_valid():
                print 'valid request'
                image=form.cleaned_data.get('image')
                caption=form.cleaned_data.get('caption')
                post=PostModel(user=user, image=image, caption=caption)
                path=str(BASE_DIR + '\\user_images\\' + post.image.url)
                print path
                client=ImgurClient('ab67b1a8a5499c7','a41e5acf05721bdb93db0a38e8c3935b49aa48bf')
                post.image_url=client.upload_from_path(path,anon=True)['link']
                post.save()
                print 'Post saved'
                return redirect('/feed/')
            else:
                print 'invalid request'
        else:
            form=PostForm()
            return render(request,'post.html', {'form':form})
    else:
        return redirect('/login/')

def like_view(request):
    user=check_validation(request)
    print 'Like view called'
    if user and request.method=='POST':
        form=LikeForm(request.POST)
        if form.is_valid():
            post_id=form.cleaned_data.get('post').id
            existing_like=LikeModel.objects.filter(post_id=post_id, user=user).first()
            print 'Validation Successful'
            if not existing_like:
                LikeModel.objects.create(post_id=post_id, user=user)
            else:
                existing_like.delete()
            return redirect('/feed/')
    else:
        return redirect('/login/')

def comment_view(request):
  user = check_validation(request)
  if user and request.method=='POST':
      form=CommentForm(request.POST)
      if form.is_valid():
          post_id = form.cleaned_data.get('post').id
          comment_text=form.cleaned_data.get('comment_text')
          comment = CommentModel.objects.create(user=user, post_id=post_id, comment_text=comment_text)
          comment.save()
          return redirect('/feed/')
      else:
          return redirect('/feed/')
  else:
    return redirect('/login')

def logout_view(request):
    if request.COOKIES.get('token'):
        user=SessionToken.objects.filter(token=request.COOKIES.get('token')).first()
        user.delete()
    return render(request,'logout.html')


