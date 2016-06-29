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

import random, string

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

	if vocab_word in [x.word for x in VocabHint.objects.all()]:
		vh = VocabHint.objects.get(word = vocab_word)
		st.add_vocab_query(vh)
		context['word'] = vh.word
		context['definition'] = vh.definition
	else:
		context['word'] = "Unknown word:  " + vocab_word
		context['definition'] = "I don't know this word.  I'm not sure how you got here."

	return render(request, 'assessment/vocab_query.html', context)

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

		# select all words not already used
		vqs = [x for x in VocabQuestion.objects.all() if x not in [y[0] for y in vresults]]

		# select those of correct k_band
		# vqs = [x for x in vqs if 
		# unfinished, not yet clear how many of each

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
		return render(request, 'assessment/passage.html', context)
	elif st.vocab_score() > .5:
		context['message'] = "You get the hard passage."
		psg = Passage.objects.get(passage_name = "hard")
		context['passage_text'] = link_vocab_hints(psg.passage_text)
		pqs = PassageQuestion.objects.filter(passage = "hard")
	else:
		context['message'] = "You get the easy passage."
		psg = Passage.objects.get(passage_name = "easy")
		context['passage_text'] = link_vocab_hints(psg.passage_text)
		pqs = PassageQuestion.objects.filter(passage = "easy")


	# process previous answer, if any
	print "POST data"
	print request.POST.keys()
	if "pickone" in request.POST.keys():
		print "Got pick one answer."
		print request.POST["pickone"]
		pq = PassageQuestion.objects.get(pq_id = request.POST["question_id"])
		st.add_passage_result(pq, request.POST["pickone"])
		st.save()
	if "pickmany" in request.POST.keys():
		print "Got pick many answer."
		print request.POST["pickmany"]
		pq = PassageQuestion.objects.get(pq_id = request.POST["question_id"])
		st.add_passage_result(pq, request.POST["pickmany"])
		st.save()

	# unfinished, needs to process other question types

	# give a question, if necessary

	results = st.get_passage_results()
	print results
	print st.passage_results

	# if they've finished the passage, just return them

	if len(set([x[0] for x in results])) == len(pqs):
		context['message'] = "Thank you for completing the assessment."
		context['passage_text'] = ""
		return render(request, 'assessment/passage.html', context)

	# if they still have questions to take, provide one

	# if this is their first question or they got the last one right or they ran out of hints, give them a new one

		# first question
	if len(results) == 0:
		set_context_from_passage_question(context, pqs[0], 0)
		return render(request, 'assessment/passage.html', context)

	previous_question = PassageQuestion.objects.get(pq_id = results[-1][0])
	previous_response = results[-1][1]
	correct_response = previous_question.correct_answer
	print previous_question
	print previous_response
	print correct_response

		# got the last one right
		# or ran out of hints
	if previous_question.question_type == "short response" or previous_question.question_type == "long response" or previous_response == correct_response or (len(results) >= 3 and results[-1][0] == results[-3][0]):
		next_q_index = len(set([x[0] for x in results]))
		set_context_from_passage_question(context, pqs[next_q_index], 0)
		return render(request, 'assessment/passage.html', context)

	# if they got the last one wrong and have hints remaining, display that one

	if results[-1][0] == results[-2][0]:
		# last two were wrong
		next_q_index = len(set([x[0] for x in results])) - 1
		set_context_from_passage_question(context, pqs[next_q_index], 2)
		return render(request, 'assessment/passage.html', context)
	else:
		# only one wrong so far
		next_q_index = len(set([x[0] for x in results])) - 1
		set_context_from_passage_question(context, pqs[next_q_index], 1)
		return render(request, 'assessment/passage.html', context)

	# Uh oh, shouldn't be here

	context['message'] = "Uh oh, something is wrong if you got this far."

	return render(request, 'assessment/passage.html', context)


def set_context_from_passage_question(context, pq, hint):
	context['question_id'] = pq.pq_id
	context['question_type'] = pq.question_type
	context['question'] = pq.prompt
	context['answer_choices'] = pq.get_answer_choices()
	if hint == 0:
		context['hint'] = ""
	elif hint == 1:
		context['hint'] = pq.hint1
	else:
		context['hint'] = pq.hint2

	# additional info for table questions

	if pq.question_type == "table":
		context['rows'] = pq.get_row_headings()
		context['cols'] = pq.get_col_headings()

	return

def link_vocab_hints(text):
	"Links all vocab words in text."
	for vocab_word in [vh.word for vh in VocabHint.objects.all()]:
		link = "<a href=\"/assessment/vocab_query/" + vocab_word + "\"/>" + vocab_word + "</a>"
		text = text.replace(vocab_word, link)
		caplink = "<a href=\"/assessment/vocab_query/" + vocab_word + "\"/>" + string.capwords(vocab_word) + "</a>"
		text = text.replace(string.capwords(vocab_word), caplink)
	return text

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
