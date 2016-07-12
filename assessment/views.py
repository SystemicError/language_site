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

import random, string, re

def indexView(request):
	context = {}
	if request.user.is_authenticated():
		context = get_index_context_from_user(request.user.username)
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
					context = get_index_context_from_user(request.user.username)
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

	if st.get_next_question_set_and_saved_responses_and_hints() == "finished":
		context['word'] = ""
		context['translation'] = ""
		context['definition'] = "No definitions are available as you have completed the assessment."
		return render(request, 'assessment/vocab_query.html', context)

	# give them the definition of this vocab word and note the query in the student database

	if vocab_word in [x.word for x in VocabHint.objects.all()]:
		vh = VocabHint.objects.get(word = vocab_word)
		st.add_vocab_query(vh)
		context['word'] = vh.word
		context['translation'] = vh.translation
		context['definition'] = vh.definition
	else:
		context['word'] = "Unknown word:  " + vocab_word
		context['translation'] = ""
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
	context['finished'] = len(vresults) >= 150
	if context['finished']:
		st.assign_passage()
		st.save()
		return render(request, 'assessment/vocab.html', context)
	else:
		# select the next word

		# select all words not already used
		unused_vqs = [x for x in VocabQuestion.objects.all() if x not in [y[0] for y in vresults]]

		# kband		nonword length
		# 1-2		3-7
		# 3-4		5-8
		# 5		5-9

		# gather unused words of first 5 kbands
		k_bands = [[] for x in range(5)]
		for band in range(5):
			k_bands[band] = [x for x in unused_vqs if x.k_band == band + 1]

		# sort nonwords into kbands
		nonwords_1_2 = [x for x in unused_vqs if x.k_band == -1 and len(x.word) >= 3 and len(x.word) <= 7]
		nonwords_3_4 = [x for x in unused_vqs if x.k_band == -1 and len(x.word) >= 5 and len(x.word) <= 8]
		nonwords_5 = [x for x in unused_vqs if x.k_band == -1 and len(x.word) >= 5 and len(x.word) <= 9]

		# figure out what k_band we should be in
		if len(vresults) < 30:
			# band 1
			w_count = len([x for x in vresults if x[0].k_band == 1])
			nw_count = len(vresults) - w_count

			if w_count == 20:
				# if we have twenty words, pick a non-word
				vq = random.choice(nonwords_1_2)
			elif nw_count == 10:
				# if we have ten non-words, pick a word
				vq = random.choice(k_bands[0])
			else:
				# otherwise, flip a 2:1 coin for word vs. nonword
				if random.randint(0, 2) == 0:
					vq = random.choice(nonwords_1_2)
				else:
					vq = random.choice(k_bands[0])
		elif len(vresults) < 60:
			# band 2
			w_count = len([x for x in vresults if x[0].k_band == 2])
			nw_count = len(vresults) - w_count - 30

			if w_count == 20:
				# if we have twenty words, pick a non-word
				vq = random.choice(nonwords_1_2)
			elif nw_count == 10:
				# if we have ten non-words, pick a word
				vq = random.choice(k_bands[1])
			else:
				# otherwise, flip a 2:1 coin for word vs. nonword
				if random.randint(0, 2) == 0:
					vq = random.choice(nonwords_1_2)
				else:
					vq = random.choice(k_bands[1])
		elif len(vresults) < 90:
			# band 3
			w_count = len([x for x in vresults if x[0].k_band == 3])
			nw_count = len(vresults) - w_count - 60

			if w_count == 20:
				# if we have twenty words, pick a non-word
				vq = random.choice(nonwords_3_4)
			elif nw_count == 10:
				# if we have ten non-words, pick a word
				vq = random.choice(k_bands[2])
			else:
				# otherwise, flip a 2:1 coin for word vs. nonword
				if random.randint(0, 2) == 0:
					vq = random.choice(nonwords_3_4)
				else:
					vq = random.choice(k_bands[2])
		elif len(vresults) < 120:
			# band 4
			w_count = len([x for x in vresults if x[0].k_band == 4])
			nw_count = len(vresults) - w_count - 90

			if w_count == 20:
				# if we have twenty words, pick a non-word
				vq = random.choice(nonwords_3_4)
			elif nw_count == 10:
				# if we have ten non-words, pick a word
				vq = random.choice(k_bands[3])
			else:
				# otherwise, flip a 2:1 coin for word vs. nonword
				if random.randint(0, 2) == 0:
					vq = random.choice(nonwords_3_4)
				else:
					vq = random.choice(k_bands[3])
		elif len(vresults) < 150:
			# band 5
			w_count = len([x for x in vresults if x[0].k_band == 5])
			nw_count = len(vresults) - w_count - 120

			if w_count == 20:
				# if we have twenty words, pick a non-word
				vq = random.choice(nonwords_5)
			elif nw_count == 10:
				# if we have ten non-words, pick a word
				vq = random.choice(k_bands[4])
			else:
				# otherwise, flip a 2:1 coin for word vs. nonword
				if random.randint(0, 2) == 0:
					vq = random.choice(nonwords_5)
				else:
					vq = random.choice(k_bands[4])

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

	# process previous answers, if any
	process_previous_passage_responses(request.POST, st)

	# give a question set, if necessary

	next_qs_sr_h = st.get_next_question_set_and_saved_responses_and_hints()

	# if they've finished the passage, just return them
	if next_qs_sr_h == "finished":
		context['message'] = "Thank you for completing the assessment."
		context['passage_text'] = ""
		return render(request, 'assessment/passage.html', context)

	# Otherwise, give the next question set

	(qset, saved_rs, hints) = next_qs_sr_h
	pqs = PassageQuestion.objects.filter(question_set = qset, passage = st.passage_assigned)
	set_context_from_passage_questions(context, pqs, saved_rs, hints)
	return render(request, 'assessment/passage.html', context)

def process_previous_passage_responses(postdata, st):
	"Takes in POST data and Student, updates student passage results."
	print "POST:"
	print postdata
	more_qs = "pickone0" in postdata.keys()
	more_qs = more_qs or " ".join(postdata.keys()).find("pickmany0") != -1
	more_qs = more_qs or "table0-0-0" in postdata.keys()
	more_qs = more_qs or "shortresponse0" in postdata.keys()
	more_qs = more_qs or "longresponse0" in postdata.keys()
	question_index = 0
	qi_str = str(question_index)
	responses = []
	while more_qs:
		# We always append a response, even if it's blank.  This way, we always
		# pass the correct number of responses
		response = ""
		if "pickone" + qi_str in postdata.keys():
			#pq_id = postdata["question_id" + qi_str]
			response = postdata["pickone" + qi_str]

		if " ".join(postdata.keys()).find("pickmany" + qi_str) != -1:
			# remember, checkboxes only send POST data when checked
			pq = PassageQuestion.objects.get(pq_id = postdata["question_id" + qi_str])
			boxes = len(pq.get_answer_choices())
			response = ""
			for box in range(boxes):
				entry_name = "pickmany" + qi_str + "-" + str(box)
				if entry_name in postdata.keys():
					response = response + str(box) + " "
			response = response.strip()

		if "table" + qi_str + "-0-0" in postdata.keys():
			pq = PassageQuestion.objects.get(pq_id = postdata["question_id" + qi_str])
			rows = len(pq.get_row_headings())
			cols = len(pq.get_col_headings())
			response = ""
			for row in range(rows):
				for col in range(cols):
					entry_name = "table" + qi_str + "-" + str(row) + "-" + str(col)
					response = response + postdata[entry_name] + " "
			response = response.strip()

		if "shortresponse" + qi_str in postdata.keys():
			#pq_id = postdata["question_id" + qi_str]
			response = postdata["shortresponse" + qi_str]

		if "longresponse" + qi_str in postdata.keys():
			#pq_id = postdata["question_id" + qi_str]
			response = postdata["longresponse" + qi_str]

		responses.append(response)

		question_index += 1
		qi_str = str(question_index)
		more_qs = "pickone" + qi_str in postdata.keys()
		more_qs = more_qs or "pickmany" + qi_str in postdata.keys()
		more_qs = more_qs or "table" + qi_str + "-0-0" in postdata.keys()
		more_qs = more_qs or "shortresponse" + qi_str in postdata.keys()
		more_qs = more_qs or "longresponse" + qi_str in postdata.keys()

	if "submit" in postdata.keys():
		if len(responses) > 0 and postdata["submit"] == "Submit and go on":
			print "Submitting"
			st.submit_question_set(responses)
			st.save()
		if postdata["submit"] == "Skip and come back":
			print "Skipping"
			st.save_and_skip_question_set(responses)
			st.save()

	return

def set_context_from_passage_questions(context, pqs, saved_rs, hints):
	"Set context for passage view."
	context['questions'] = []
	for i in range(len(pqs)):
		question = {}
		pq = pqs[i]
		hint = hints[i]

		question['id'] = pq.pq_id
		question['type'] = pq.question_type
		question['prompt'] = pq.prompt
		question['answer_choices'] = pq.get_answer_choices()

		# encode saved responses as appropriate to question type
		if len(saved_rs) > i:
			saved_response = saved_rs[i]
			question['saved_response'] = format_saved_response(saved_response, pq)

		# provide hint(s)
		if hint == 0:
			question['hint'] = ""
		elif hint == 1:
			question['hint'] = pq.hint1
		elif hint == 2:
			question['hint'] = pq.hint2
		elif hint == -1:
			question['hint'] = "That is correct!"
		else:
			question['hint'] = "You are out of attempts for this question."

		# additional info for table questions

		if pq.question_type == "table":
			question['rows'] = pq.get_row_headings()
			question['cols'] = pq.get_col_headings()

		context['questions'].append(question)

	return

def format_saved_response(saved_response, pq):
	"Formats a saved response so that the template can easily render it."
	if pq.question_type == "pick one":
		return int(saved_response)
	elif pq.question_type == "pick many":
		return [int(x) for x in saved_response.strip().split()]
	elif pq.question_type == "table":
		return [int(x) for x in saved_response.strip().split()]
	elif pq.question_type == "short response":
		return saved_response
	elif pq.question_type == "long response":
		return saved_response
	return ""

def link_vocab_hints(text):
	"Links all vocab words in text."
	for vocab_word in [vh.word for vh in VocabHint.objects.all()]:
		pieces = []
		pattern = r"[^A-Za-z]" + vocab_word + r"[^A-Za-z]"
		previous = 0
		for m in re.finditer(pattern, text):
			pieces.append(text[previous:m.start() + 1])
			previous = m.end() - 1
		link = "<a href=\"/assessment/vocab_query/" + vocab_word + "\"/>" + vocab_word + "</a target=\"_blank\">"
		if previous != 0:
			pieces.append(text[previous:])
			text = link.join(pieces)

		pieces = []
		pattern = r"[^A-Za-z]" + string.capwords(vocab_word) + r"[^A-Za-z]"
		previous = 0
		for m in re.finditer(pattern, text):
			pieces.append(text[previous:m.start() + 1])
			previous = m.end() - 1
		caplink = "<a href=\"/assessment/vocab_query/" + vocab_word + "\"/>" + string.capwords(vocab_word) + "</a target=\"_blank\">"
		if previous != 0:
			pieces.append(text[previous:])
			text = caplink.join(pieces)
	return text

def get_index_context_from_user(username):
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
			if st.get_next_question_set_and_saved_responses_and_hints() == "finished":
				context['content'] = "You have completed the assessment.  Please log out."
				context['link'] = "logout"
			else:
				context['scores'] = [st.vocab_score(x + 1)*100.0 for x in range(5)]
				context['overall_score'] = st.vocab_score()*100.0
				context['content'] = "It's time to take the passage test."
				context['link'] = "passage"
	else:
		context['content'] = "Welcome to your first login.  I'm adding you to the database.  Go take the vocab quiz."
		context['link'] = "vocab"
		st = Student()
		st.name = username
		st.save()
	return context
