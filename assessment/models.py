from django.db import models

from django.utils.encoding import python_2_unicode_compatible

import datetime
from django.utils import timezone

@python_2_unicode_compatible
class VocabQuestion(models.Model):
	item_id = models.IntegerField(unique=True,default=0)
	k_band = models.IntegerField(default=0)
	word = models.CharField(max_length = 64)
	is_word = models.BooleanField(default=False)
	def __str__(self):
		return self.word

@python_2_unicode_compatible
class Student(models.Model):
	name = models.CharField(max_length = 64)

	vocab_results = {}  # populate with (question, response)

	def vocab_score(self):
		num_correct = len([x for x in self.vocab_results.keys() if self.vocab_results[x] == VocabQuestion.objects.get(word=x).is_word])
		if len(self.vocab_results) != 0:
			return float(num_correct)/len(self.vocab_results)
		else:
			return -1
	def __str__(self):
		return self.name

