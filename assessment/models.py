from django.db import models

from django.utils.encoding import python_2_unicode_compatible

import datetime, copy
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
	vocab_results = models.TextField(default = "")

	# populate with (question_id, response) pairs
	# question_id not unique, as some questions have multiple attempts
	passage_results = models.TextField(default = "")

	# the question sets, in order, to be taken
	pq_set_queue = models.CharField(default = "", max_length = 1024)

	# vocabhint lookups, and their counts
	# want to treat these like a dictionary/key
	vocab_query_counts = models.TextField(default = "")

	passage_assigned = models.CharField(max_length = 64, default = "")

	def get_next_question_set_and_saved_responses_and_hints(self):
		"returns (question_set, saved_responses, hints)"

		if self.passage_assigned == "":
			return (None, [], [])

		(question_set, saved_responses) = self.pq_set_queue_peek()

		hints = []
		pqs = PassageQuestion.objects.filter(passage = self.passage_assigned, pq_set = question_set)
		p_results = self.get_passage_results()
		qset_results = [p_results[x.pq_id] for x in pqs]

		for i in range(len(pqs)):
			# check if each question has been answered, and whether it's due for a hint
			if len(qset_results[i]) == 0:
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
		(question_set, responses) = self.pq_set_queue_peek()
		pqs = PassageQuestion.objects.filter(passage_id=self.assigned_passage,pq_set=question_set)
		move_on = True
		for i in range(len(responses)):
			self.add_passage_result(pqs[i], responses[i])
			if not self.pq_complete(pqs[i]):
				move_on = False
		if move_on:
			self.pq_set_dequeue()
		return

	def save_and_skip_question_set(self, responses):
		"Dequeues and enqueues the question set with current responses"
		question_set = self.pq_set_dequeue()[0]
		self.pq_set_enqueue(question_set, responses)
		return

	def pq_set_enqueue(self, question_set, responses):
		"Enqueues the question set."
		entry = "<question_set><set_id>" + question_set + "</set_id>"

		for response in responses:
			entry = entry + "<response>" + response + "</response>"

		entry = entry + "</quesiton_set>"
		self.pq_set_queue = self.pq_set_queue + entry
		return

	def pq_set_dequeue(self):
		"Returns dequeue of (question_set, responses)"
		# Remove first entry from queue
		entry = split_by_tag(self.pq_set_queue, "question_set")[0]
		self.pq_set_queue = self.pq_set_queue[len(entry):]

		# read entry
		question_set = split_by_tag(entry, "set_id")[0]
		responses = split_by_tag(entry, "response")

		return (question_set, responses)

	def pq_set_queue_peek(self):
		"Gets first entry in pq_set_queue without modifying."
		entry = split_by_tag(self.pq_set_queue, "question_set")[0]
		question_set = split_by_tag(entry, "set_id")[0]
		responses = split_by_tag(entry, "response")
		return (question_set, responses)

	def add_passage_result(self, pq, response):
		"Adds question_id of pq and response to passage_results."
		result = "<response question_id="
		result = result + str(pq.pq_id)
		result = result + ">" + response + "</response>"
		self.passage_results = self.passage_results + result
		return

	def get_passage_results(self):
		"Returns a dictionary of passage question_ids to lists of responses."
		results = {}
		results_string = copy.deepcopy(self.passage_results)
		first_result = results_string.find("<response question_id=")
		while first_result != -1:
			results_string = results_string[first_result + len("<response question_id="):]
			tag_close_index = results_string.find(">")
			#if tag_close_index == -1:
				#print("No closing > on result string, panic!")
			question_id = results_string[:tag_close_index]
			results_string = results_string[tag_close_index + 1:]
			result_end = results_string.find("</response>")

			if not question_id in results.keys():
				results[question_id] = []
			results[question_id].append(results_string[:result_end])

			first_result = results_string.find("<response question_id=")
		return results

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
		pq_sets = [pq.question_set for pq in PassageQuestion.objects.filter(passage=self.passage_assigned)]
		for pq_set in pq_sets:
			entry = "<question_set><set_id>" + pq_set + "</set_id></question_set>"
			self.pq_set_queue = self.pq_set_queue + entry
		return

	def add_vocab_query(self, vh):
		"Adds one to query of vocabHint vh (or creates new record if previously zero)."
		# words and counts are ; separated
		word_index = self.vocab_query_counts.find(vh.word)

		if word_index == -1:
			self.vocab_query_counts = self.vocab_query_counts + vh.word + ";1;"
			return
		# okay, it's already in the list
		count_index = self.vocab_query_counts.find(";",word_index) + 1
		count_end = self.vocab_query_counts.find(";",count_index)

		count = int(self.vocab_query_counts[count_index:count_end])
		count = count + 1

		self.vocab_query_counts = self.vocab_query_counts[:count_index] + str(count) + self.vocab_query_counts[count_end:]
		return

	def get_vocab_words_queried(self):
		"Returns a dictionary of vocabHint.words to counts."
		query_counts = {}
		words_and_counts = self.vocab_query_counts.split(";")
		for i in range(0, len(words_and_counts) - 1, 2):
			word = words_and_counts[i]
			count = int(words_and_counts[i + 1])
			query_counts[word] = count
		return query_counts

	def add_vocab_result(self, vq, response):
		self.vocab_results = self.vocab_results + str(vq.word) + "," + str(response) + ";"
		return

	def get_vocab_results(self):
		vr = []
		if self.vocab_results.find(";") == -1:
			return []

		for entry in self.vocab_results.split(";")[:-1]:
			wd = entry.split(",")[0]
			response = entry.split(",")[1]
			vq = VocabQuestion.objects.get(word = wd)
			if response == "True":
				response = True
			else:
				response = False
			vr.append((vq, response))
		return vr

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
	question_set = models.CharField(max_length = 16, default = "")

	# what's the name of our associated passage?
	passage = models.CharField(max_length = 64, default = "")

	# pick one, pick many, table, short response, long response
	question_type = models.CharField(max_length = 64)

	# includes the quesiton, or, if table, the rows, columns in xmlish tags
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
		"Return correct answer as int, if pick one, tuple if pick many or table."
		if self.question_type == "pick one":
			return int(self.correct_answer)
		elif self.question_type == "pick many" or self.question_type == "table":
			return tuple([int(x) for x in self.correct_answer.split()])
		else:
			return None

	def get_row_headings(self):
		"For a table type question, gets row headings."
		if self.question_type != "table":
			return None
		rows = []
		rows_string = copy.deepcopy(self.prompt)
		first_row = rows_string.find("<row>")
		while first_row != -1:
			rows_string = rows_string[first_row + len("<row>"):]
			row_end = rows_string.find("</row>")
			rows.append(rows_string[:row_end])
			first_row = rows_string.find("<row>")
		return rows
		

	def get_col_headings(self):
		"For a table type question, gets col headings."
		if self.question_type != "table":
			return None
		cols = []
		cols_string = copy.deepcopy(self.prompt)
		first_col = cols_string.find("<col>")
		while first_col != -1:
			cols_string = cols_string[first_col + len("<col>"):]
			col_end = cols_string.find("</col>")
			cols.append(cols_string[:col_end])
			first_col = cols_string.find("<col>")
		return cols
		

	def __str__(self):
		return self.prompt

# helper function
def split_by_tag(text, tag):
	"Takes in text and returns an array of strings of stuff between <tag></tag>"
	items = []
	open_tag = text.find("<" + tag + ">")
	while open_tag != -1:
		text = text[open_tag + len(tag) + 2:]
		close_tag = text.find("</" + tag + ">")

		items.append(text[:close_tag])

		open_tag = text.find("<" + tag + ">")
	return items
