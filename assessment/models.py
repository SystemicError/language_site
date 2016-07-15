from django.db import models

from django.utils.encoding import python_2_unicode_compatible

import datetime, copy, json
from django.utils import timezone

@python_2_unicode_compatible
class VocabQuestion(models.Model):
	item_id = models.IntegerField(unique=True, default=0)
	k_band = models.IntegerField(default=0)
	word = models.CharField(unique=True, max_length = 64)
	is_word = models.BooleanField(default=False)

	def __str__(self):
		return self.word

@python_2_unicode_compatible
class Student(models.Model):
	name = models.CharField(unique=True, max_length = 64)

	# populate with (question, response) pairs
	vocab_results = models.TextField(default = "[]")

	# populate with (question_id, response) pairs
	# question_id not unique, as some questions have multiple attempts
	passage_results = models.TextField(default = "{}")

	# the question sets, in order, to be taken, with saved responses
	pq_set_queue = models.TextField(default = "[]")

	# vocabhint lookups, and their counts
	# want to treat these like a dictionary/key
	vocab_query_counts = models.TextField(default = "{}")

	passage_assigned = models.CharField(max_length = 64, default = "")

	def get_next_question_set_and_saved_responses_and_hints(self):
		"returns (question_set, saved_responses, hints)"

		if self.passage_assigned == "":
			return "unassigned"

		queue = json.loads(self.pq_set_queue)

		# if they're done with the assessment
		if len(queue) == 0:
			return "finished"

		(question_set, saved_responses) = queue[0]

		hints = []
		pqs = PassageQuestion.objects.filter(passage = self.passage_assigned, question_set = question_set)
		p_results = self.get_passage_results()

		qset_results = []
		for pq in pqs:
			if pq.pq_id in p_results.keys():
				qset_results.append(p_results[pq.pq_id])
			else:
				qset_results.append([])

		for i in range(len(pqs)):
			# check if each question has been answered, and whether it's due for a hint
			if len(qset_results[i]) == 0 or pqs[i].question_type in ["short response", "long response"]:
				hint = 0 # never attempted
			elif len(qset_results[i]) > 0 and qset_results[i][-1] == pqs[i].correct_answer:
				hint = -1 # correct
			elif len(qset_results[i]) == 1 and qset_results[i][-1] != pqs[i].correct_answer and pqs[i].get_number_of_hints() > 0:
				hint = 1 # wrong once
			elif len(qset_results[i]) == 2 and qset_results[i][-1] != pqs[i].correct_answer and pqs[i].get_number_of_hints() > 1:
				hint = 2 # wrong twice
			else:
				hint = -2 # out of hints

			hints.append(hint)
			

		return (question_set, saved_responses, hints)

	def has_completed_passage(self):
		"Returns True if passage complete."
		if self.passage_assigned != "" and len(json.loads(self.pq_set_queue)) == 0:
			return True
		else:
			return False

	def pq_complete(self, pq):
		"Checks if passage question finished, either due to too many wrong or a right answer."
		results = self.get_passage_results()[pq.pq_id]
		if len(results) == 0:
			return False
		if len(results) > pq.get_number_of_hints():
			return True
		if results[-1] == pq.correct_answer:
			return True
		return False

	def submit_question_set(self, responses):
		"Adds each of the elements of responses as a passage result."
		# We may discard saved responses
		queue = json.loads(self.pq_set_queue)
		question_set = queue[0][0]
		pqs = PassageQuestion.objects.filter(passage=self.passage_assigned,question_set=question_set)
		move_on = True
		for i in range(len(responses)):
			self.add_passage_result(pqs[i], responses[i])
			if not self.pq_complete(pqs[i]):
				move_on = False
		queue.pop(0)
		if not move_on:
			# prepend the same question set on to the queue, but with our given responses
			entry = (question_set, responses)
			queue.insert(0, entry)
		self.pq_set_queue = json.dumps(queue)
		return

	def save_and_skip_question_set(self, responses):
		"Dequeues and enqueues the question set with current responses"
		question_set = self.pq_set_dequeue()[0]
		self.pq_set_enqueue(question_set, responses)
		return

	def save_and_dont_skip_question_set(self, responses):
		"Saves a set of responses without advancing the queue."
		queue = json.loads(self.pq_set_queue)
		queue[0][1] = responses
		self.pq_set_queue = json.dumps(queue)
		return

	def pq_set_enqueue(self, question_set, responses):
		"Enqueues the question set."
		queue = json.loads(self.pq_set_queue)
		queue.append((question_set, responses))
		self.pq_set_queue = json.dumps(queue)
		return

	def pq_set_dequeue(self):
		"Returns dequeue of (question_set, responses)"
		queue = json.loads(self.pq_set_queue)

		# Remove first entry from queue
		entry = queue.pop(0)

		# read entry
		question_set = entry[0]
		responses = entry[1]

		self.pq_set_queue = json.dumps(queue)
		return (question_set, responses)

	def pq_set_queue_peek(self):
		"Returns first element of pq_set_queue with modifying."
		queue = json.loads(self.pq_set_queue)
		return queue[0]

	def add_passage_result(self, pq, response):
		"Adds response to passage_results[pq.pq_id]."
		results = self.get_passage_results()
		if not pq.pq_id in results.keys():
			results[pq.pq_id] = []
		results[pq.pq_id].append(response)
		self.passage_results = json.dumps(results)
		return

	def get_passage_results(self):
		"Returns a dictionary of passage question_ids to lists of responses."
		return json.loads(self.passage_results)

	def assign_passage(self):
		"Assigns passage based on vocab quiz results."
		if self.vocab_score() == -1:
			#print("Error, can't assign passage without complete vocab score.")
			self.passage_assigned = ""
			return
		elif self.vocab_score(2) >= .85:
			self.passage_assigned = "hard"
		else:
			self.passage_assigned = "easy"
		pq_sets = set([pq.question_set for pq in PassageQuestion.objects.filter(passage=self.passage_assigned)])
		self.pq_set_queue = json.dumps([(x, []) for x in pq_sets])
		return

	def add_vocab_query(self, vh):
		"Adds one to query of vocabHint vh (or creates new record if previously zero)."
		qset = self.pq_set_queue_peek()[0]
		query_counts = self.get_vocab_words_queried()
		if vh.word in query_counts.keys():
			if qset in query_counts[vh.word].keys():
				query_counts[vh.word][qset] += 1
			else:
				query_counts[vh.word][qset] = 1
		else:
			query_counts[vh.word] = {qset: 1}
		self.vocab_query_counts = json.dumps(query_counts)
		return

	def get_vocab_words_queried(self):
		"Returns a dictionary of vocabHint.words to counts."
		query_counts = json.loads(self.vocab_query_counts)
		return query_counts

	def add_vocab_result(self, vq, response):
		self.vocab_results = json.dumps(json.loads(self.vocab_results) + [(vq.word, response)])
		return

	def get_vocab_results(self):
		results = [(VocabQuestion.objects.get(word=x[0]), x[1]) for x in json.loads(self.vocab_results)]
		return results

	def vocab_score(self, k_band=-1):
		"Returns score for a given k band (or overall by default)."
		vresults = self.get_vocab_results()
		if len(vresults) < 150:
			return -1
		if k_band > 0:
			vresults = vresults[(k_band - 1)*30:k_band*30]
		num_correct_words = len([x for x in vresults if x[0].is_word and x[1]])
		num_incorrect_nonwords = len([x for x in vresults if (not x[0].is_word) and x[1]])
		score = num_correct_words - 2*num_incorrect_nonwords
		if k_band > 0:
			return score/20.0
		else:
			return score/100.0

	def __str__(self):
		return self.name


@python_2_unicode_compatible
class VocabHint(models.Model):
	# For giving clues to highlighted words in the passage
	word = models.CharField(unique=True, max_length = 64)
	translation = models.CharField(default = "", max_length = 64)
	definition = models.TextField(default = "")
	def __str__(self):
		return self.word

@python_2_unicode_compatible
class Passage(models.Model):
	passage_id = models.IntegerField(unique=True, default = 0)
	passage_name = models.CharField(max_length = 64, default = "")
	passage_text = models.TextField(default = "")
	def __str__(self):
		return self.passage_name

@python_2_unicode_compatible
class PassageQuestion(models.Model):
	pq_id = models.CharField(unique=True, max_length = 16, default = "")

	# question set
	question_set = models.IntegerField(default = 0)

	# what's the name of our associated passage?
	passage = models.CharField(max_length = 64, default = "")

	# pick one, pick many, short response, long response
	question_type = models.CharField(max_length = 64)

	# the question text
	prompt = models.TextField(default = "")

	# two hints in the event of a wrong answer
	hint1 = models.TextField(default = "")
	hint2 = models.TextField(default = "")

	# answer choices, enclosed with <choice> tags
	answer_choices = models.TextField(default = "")

	# correct answer, needed to determine when to give hints for multiple choice questions
	correct_answer = models.CharField(max_length = 32, default = "")

	def get_number_of_hints(self):
		if self.hint2 != "None":
			return 2
		if self.hint1 != "None":
			return 1
		return 0

	def get_answer_choices(self):
		"Returns the answer choices as a list, unless open answer."
		if self.question_type == "long response" or self.question_type == "short response":
			return None
		choices = []
		choices_string = copy.deepcopy(self.answer_choices)
		first_choice = choices_string.find("<choice>")
		while first_choice != -1:
			choices_string = choices_string[first_choice + len("<choice>"):]
			choice_end = choices_string.find("</choice>")
			choices.append(choices_string[:choice_end])
			first_choice = choices_string.find("<choice>")
		return choices

	def get_correct_answer(self):
		"Return correct answer as int, if pick one, tuple if pick many."
		if self.question_type == "pick one":
			return int(self.correct_answer)
		elif self.question_type == "pick many":
			return tuple([int(x) for x in self.correct_answer.split()])
		else:
			return None

	def __str__(self):
		return self.prompt
