from django.shortcuts import render

from django.http import HttpResponseRedirect, HttpResponse
from django.template import loader
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.views import generic
from django.utils import timezone

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from .models import *

import random

def indexView(request):
	#print request.POST
	#print request.POST.keys()
	context = {}
	if request.user.is_authenticated():
		print "Got authenticated user."
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
				if user.is_authenticated():
					print "Logged you in."
					context = get_user_context(request.user.username)
			else:
				# if not, try again
				context = {'greeting':  "Invalid login info.  Please try again.", 'content': "", 'link': "login"}
		else:
			# if not, redirect to login
			context = {'greeting':  "You are not logged in.  Please login.", 'content': "", 'link': "login"}

	return render(request, 'assessment/index.html', context)

def loginView(request):
	context = {}
	return render(request, 'assessment/login.html', context)

def logoutView(request):
	context = {}
	logout(request)
	return render(request, 'assessment/logout.html', context)

@login_required(login_url='/assessment/login')
def vocabQueryView(request, vocab_word):
	# for vocab lookups during the passage
	context = {}
	st = Student.objects.get(name = request.user.username)

	# give them the definition of this vocab word and note the query in the student database

	vh = VocabHint.objects.get(word = vocab_word)

	# unfinished, need to account of invalid word looked up

	st.add_vocab_query(vh)

	context['word'] = vh.word
	context['definition'] = vh.definition

	return context

@login_required(login_url='/assessment/login')
def vocabView(request):
	# for vocab quiz questions
	context = {}
	st = Student.objects.get(name = request.user.username)
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
		vq = VocabQuestion.objects.get(word = previous_word)
		st.add_vocab_result(vq, previous_response)
		st.save()

	# present a new question, or, if they're done, present none

	vresults = st.get_vocab_results()
	context['num_complete'] = len(vresults)
	context['finished'] = len(vresults) >= 30
	if context['finished']:
		return render(request, 'assessment/vocab.html', context)
	else:
		# select the next word
		# unfinished -- doesn't currently select a unique word
		# unfinished -- doesn't select by band/frequency
		vqs = [x for x in VocabQuestion.objects.all() if x not in [y[0] for y in vresults]]
		vq = vqs[random.randint(0, len(vqs) - 1)]
		context['word'] = vq.word
	return render(request, 'assessment/vocab.html', context)

@login_required(login_url='/assessment/login')
def passageView(request):
	context = {}
	st = Student.objects.get(name = request.user.username)
	# if vocab_score == -1, they shouldn't be here
	if st.vocab_score() == -1:
		context['message'] = "You need to go back to the index."
	elif st.vocab_score() > .5:
		context['message'] = "You get the hard passage."
		psg = Passage.objects.get(passage_id = 0)
		context['passage_text'] = psg.passage_text
	else:
		context['message'] = "You get the easy passage."
		psg = Passage.objects.get(passage_id = 1)
		context['passage_text'] = psg.passage_text

	return render(request, 'assessment/passage.html', context)




def get_user_context(username):
	context = {}
	context['greeting'] = "Welcome, " + username + "."
	# if they're not in the database, add them, and direct them to vocab quiz
	# if they are in the database, see how much progress they've made and direct them
	if username in [x.name for x in Student.objects.all()]:
		st = Student.objects.get(name = username)
		if len(st.get_vocab_results()) < 30:
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
