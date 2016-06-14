from django.shortcuts import render

from django.http import HttpResponseRedirect, HttpResponse
from django.template import loader
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.views import generic
from django.utils import timezone

from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required

from .models import *

import random

def indexView(request):
	#print request.POST
	#print request.POST.keys()
	if request.user.is_authenticated():
		context = get_user_context(request.user.username)
	else:
		# have we come here from the login page?
		if 'login' in request.POST.keys():
			# if so, try to log in
			username = request.POST['login']
			password = request.POST['password']
			print "Attempting to authenticate . . ."
			user = authenticate(username = username, password = password)

			print user
			# is this a real account?
			if user is not None:
				# if so, log them in
				login(request, user)
			else:
				# if not, try again
				context = {'greeting':  "Invalid login info.  Please try again.", 'content': "", 'link': "login"}
		else:
			# if not, redirect to login
			context = {'greeting':  "You are not logged in.  Please login.", 'content': "", 'link': "login"}

	return render(request, 'assessment/index.html', context)

	#user = False
	#if 'login' in request.POST.keys():
	#	username = request.POST['login']
	#	password = request.POST['password']
	#	print "Attempting to authenticate . . ."
	#	user = authenticate(username = username, password = password)
	#	print user
	#if user is not None and user is not False:
	#	login(request, user)
	#	if user.is_active:
	#		# Advise progress
	#		context = get_user_context(user.username)
	#	else:
	#		# disabled account
	#		context = {'greeting':  "Account disabled!  I don't trust you.", 'content': "", 'link': "login"}
	#else:
		#invalid login, no content
	#	context = {'greeting':  "You are not logged in.  Please login.", 'content': "", 'link': "login"}
	#return render(request, 'assessment/index.html', context)

def loginView(request):
	context = {}
	return render(request, 'assessment/login.html', context)

@login_required
def vocabView(request):
	context = {}
	st = Student(name = request.user.username)
	print "Student:" + str(st)

	# process previous answer, if any
	print request.POST
	print request.POST.keys()

	if "is_word" in request.POST.keys():
		print request.POST["is_word"]
		previous_response = (request.POST["is_word"] == "yes")
		previous_word = request.POST["word"]
		print "Previous response was " + str(previous_response)
		print "Previous word was:" + previous_word
		st.vocab_results[previous_word] = previous_response
		st.save()

	# present a new question, or, if they're done, present none

	context['num_complete'] = len(st.vocab_results)
	context['finished'] = len(st.vocab_results) >= 10
	if context['finished']:
		return render(request, 'assessment/vocab.html', context)
	else:
		vqs = VocabQuestion.objects.all()
		vq = vqs[random.randint(0, len(vqs) - 1)]
		context['word'] = vq.word
	return render(request, 'assessment/vocab.html', context)

def passageView(request):
	context = {}
	return render(request, 'assessment/passage.html', context)




def get_user_context(username):
	context = {}
	context['greeting'] = "Welcome, " + username + "."
	# if they're not in the database, add them, and direct them to vocab quiz
	# if they are in the database, see how much progress they've made and direct them
	if username in [x.name for x in Student.objects.all()]:
		st = Student(name = username)
		if st.vocab_score() == -1:
			context['content'] = "You need to take the vocab test."
			context['link'] = "vocab"
		else:
			context['content'] = "You took the test and got " + str((st.vocab_score()*100)) + "%.  It's time to take the passage test."
			context['link'] = "passage"
	else:
		context['content'] = "Welcome to your first login.  I'm adding you to the database.  Go take the vocab quiz."
		context['link'] = "vocab"
		st = Student()
		st.name = username
		st.save()
	return context
