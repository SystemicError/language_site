from django.db import models

from django.utils.encoding import python_2_unicode_compatible

import datetime
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

	def add_vocab_result(self, vq, response):
		self.vocab_results = self.vocab_results + str(vq.word) + "," + str(response) + ";"
		print "Updated vocab results:"
		print self.vocab_results

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

