from django.shortcuts import render

from django.http import HttpResponseRedirect, HttpResponse
from django.template import loader
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.views import generic
from django.utils import timezone

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from django.core.exceptions import ObjectDoesNotExist

from .models import *

import random, string

def indexView(request):
	#print request.POST
	#print request.POST.keys()
	context = {}
	if request.user.is_authenticated():
		#print "Got authenticated user."
		context = get_user_context(request.user.username)
	else:
		# have we come here from the login page?
		if 'login' in request.POST.keys():
			# if so, try to log in
			username = request.POST['login']
			password = request.POST['password']
			user = authenticate(username = username, password = password)

			# is this a real account?
			if user is not None:
				# if so, log them in
				login(request, user)
				if user.is_authenticated():
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

	# reject users who are done with the assessment

	if st.has_completed_passage():
		context['word'] = ""
		context['definition'] = "No definitions are available as you have completed the assessment."
		return render(request, 'assessment/vocab_query.html', context)

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

	# process previous answer, if any

	if "is_word" in request.POST.keys():
		previous_response = (request.POST["is_word"] == "yes")
		previous_word = request.POST["word"]
		vq = VocabQuestion.objects.get(word = previous_word)
		st.add_vocab_result(vq, previous_response)
		st.save()

	# present a new question, or, if they're done, present none

	vresults = st.get_vocab_results()
	context['num_complete'] = len(vresults)
	context['finished'] = len(vresults) >= 30
	if context['finished']:
		st.assign_passage()
		st.save()
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
	context['message'] = "You get the " + st.passage_assigned + " passage."

	try:
		psg = Passage.objects.get(passage_name = st.passage_assigned)
	except ObjectDoesNotExist:
		context['message'] = "Error:  can't find assigned passage \'" + st.passage_assigned + "\'"
		return render(request, 'assessment/passage.html', context)

	context['passage_text'] = link_vocab_hints(psg.passage_text)
	pqs = PassageQuestion.objects.filter(passage = st.passage_assigned)

	# process previous answer, if any
	if "pickone" in request.POST.keys():
		pq = PassageQuestion.objects.get(pq_id = request.POST["question_id"])
		st.add_passage_result(pq, request.POST["pickone"])
		st.save()
	if "pickmany" in " ".join(request.POST.keys()):
		# remember, checkboxes only send POST data when checked
		pq = PassageQuestion.objects.get(pq_id = request.POST["question_id"])
		boxes = len(pq.get_correct_answer())
		response = ""
		for box in range(boxes):
			entry_name = "pickmany" + str(box)
			if entry_name in request.POST.keys():
				response = response + str(box) + " "
		response = response.strip()
		st.add_passage_result(pq, response)
		st.save()

	if "table0-0" in request.POST.keys():
		pq = PassageQuestion.objects.get(pq_id = request.POST["question_id"])
		rows = len(pq.get_row_headings())
		cols = len(pq.get_col_headings())
		response = ""
		for row in range(rows):
			for col in range(cols):
				entry_name = "table" + str(row) + "-" + str(col)
				response = response + request.POST[entry_name] + " "
		response = response.strip()
		st.add_passage_result(pq, response)
		st.save()

	if "shortresponse" in request.POST.keys():
		pq = PassageQuestion.objects.get(pq_id = request.POST["question_id"])
		st.add_passage_result(pq, request.POST["shortresponse"])
		st.save()

	if "longresponse" in request.POST.keys():
		pq = PassageQuestion.objects.get(pq_id = request.POST["question_id"])
		st.add_passage_result(pq, request.POST["longresponse"])
		st.save()

	# unfinished, needs to process other question types

	# give a question, if necessary

	results = st.get_passage_results()


	# if they still have questions to take, provide one

	(pq, hint) = st.get_next_passage_question_and_hint()

	# if they've finished the passage, just return them
	if pq == None:
		context['message'] = "Thank you for completing the assessment."
		context['passage_text'] = ""
		return render(request, 'assessment/passage.html', context)

	# Otherwise, give the next question

	set_context_from_passage_question(context, pq, hint)
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
		link = "<a href=\"/assessment/vocab_query/" + vocab_word + "\"/>" + vocab_word + "</a target=\"_blank\">"
		text = text.replace(vocab_word, link)
		caplink = "<a href=\"/assessment/vocab_query/" + vocab_word + "\"/>" + string.capwords(vocab_word) + "</a target=\"_blank\">"
		text = text.replace(string.capwords(vocab_word), caplink)
	return text

def get_user_context(username):
	context = {}
	context['greeting'] = "Welcome, " + username + "."
	# if they're not in the database, add them, and direct them to vocab quiz
	# if they are in the database, see how much progress they've made and direct them
	if username in [x.name for x in Student.objects.all()]:
		st = Student.objects.get(name = username)
		if st.passage_assigned == "":
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
