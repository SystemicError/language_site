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
	passage_results = models.TextField(default = "")

	# vocabhint lookups, and their counts
	# want to treat these like a dictionary/key
	vocab_query_counts = models.TextField(default = "")


	def add_passage_result(self, pq, response):
		"Adds question_id of pq and response to passage_results."
		result = "<response question_id="
		result = result + str(pq.question_id)
		result = result + ">" + response + "</response>"
		self.passage_results = self.passage_results + result
		return

	def get_passage_results(self):
		"Returns a list of tuples of the passage question_ids and responses."
		results = []
		results_string = copy.deepcopy(self.passage_results)
		first_result = results_string.find("<response question_id =")
		while first_result != -1:
			results_string = results_string[first_result + len("<response question_id="):]
			tag_close_index = results_string.find(">")
			if tag_close_index == -1:
				print "No closing > on result string, panic!"
			question_id = int(results_string[:tag_close_index])
			results_string = results_string[tag_close_index + 1:]
			result_end = results_string.find("</response>")
			results.append((question_id, results_string[:result_end]))
		return results

		


	def add_vocab_query(self, vh):
		"Adds one to query of vocabHint vh (or creates new record if previously zero)."
		# words and counts are ; separated
		word_index = self.vocab_query_counts.find(vh.word)

		if word_index == -1:
			self.vocab_query_counts = self.vocab_query_counts + vh.word + ";1"
			return
		# okay, it's already in the list
		count_index = self.vocab_query_counts.find(";",word_index) + 1
		count_end = self.vocab_query_counts.find(";",count_index)

		count = int(self.vocab_query_counts[count_index:count_end])
		count = count + 1

		self.vocab_query_counts = self.vocab_query_counts[count_index:] + str(count) + self.vocab_query_counts[count_end:]
		return

	def get_vocab_words_queried(self):
		"Returns a dictionary of vocabHints and counts."
		query_counts = {}
		words_and_counts = self.vocab_query_counts.split(";")
		for i in range(0, len(words_and_counts), 2):
			word = words_and_counts[i]
			count = int(words_and_counts[i + 1])
			query_counts[word] = count
		return query_counts

	def add_vocab_result(self, vq, response):
		self.vocab_results = self.vocab_results + str(vq.word) + "," + str(response) + ";"
		print "Updated vocab results:"
		print self.vocab_results
		return

	def get_vocab_results(self):
		vr = []
		if self.vocab_results.find(";") == -1:
			print "Empty vocab results."
			return []

		print "Vocab split:"
		print self.vocab_results.split(";")

		for entry in self.vocab_results.split(";")[:-1]:
			print "Entry:"
			print entry
			wd = entry.split(",")[0]
			response = entry.split(",")[1]
			vq = VocabQuestion.objects.get(word = wd)
			if response == "True":
				response = True
			else:
				response = False
			vr.append((vq, response))
		return vr

	def vocab_score(self):
		num_correct = 0
		vresults = self.get_vocab_results()
		for vr in vresults:
			if vr[0].is_word == vr[1]:
				num_correct += 1
		if len(vresults) != 0:
			return float(num_correct)/len(vresults)
		else:
			return -1
	def __str__(self):
		return self.name


@python_2_unicode_compatible
class VocabHint(models.Model):
	# For giving clues to highlighted words in the passage
	word = models.CharField(unique=True, max_length = 64)
	definition = models.TextField(default = "")
	def __str__(self):
		return self.word

@python_2_unicode_compatible
class Passage(models.Model):
	passage_id = models.IntegerField(unique=True, default = 0)
	passage_text = models.TextField(default = "")
	def __str__(self):
		return self.passage_id

@python_2_unicode_compatible
class PassageQuestion(models.Model):
	pq_id = models.IntegerField(unique=True, default = 0)

	# pick one, pick many, table, short response, long response
	question_type = models.CharField(max_length = 64)

	# includes the quesiton, or, if table, the rows, columns in xmlish tags
	prompt = models.TextField(default = "")

	# answer choices, enclosed with <choice> tags
	answer_choices = models.TextField(default = "")

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

