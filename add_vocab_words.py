#!/usr/bin/env python
import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "language_site.settings")
from django.core.management import execute_from_command_line


import django
from assessment.models import VocabQuestion
django.setup()


print "Reading text file."
try:
	fin = open("vocab.txt")
	lines = fin.readlines()
except IOError:
	print "Couldn't open vocab file!"
	sys.exit(1)
fin.close()

print "Adding words."

for line in lines[1:]:
	fields = line.split()
	item_id = int(fields[0])
	if fields[1] == "na":
		k_band = -1
	else:
		k_band = int(fields[1])
	word = fields[2]
	if fields[3] == "n":
		is_word = False
	else:
		is_word = True

	if item_id in [vq.item_id for vq in VocabQuestion.objects.all()]:
		print "Skipping " + word + " (already in database) . . ."
	else:

		print "Adding word:  " + str(item_id) + ", " + str(k_band) + ", " + str(word) + ", " + str(is_word)

		vq = VocabQuestion()
		vq.item_id = item_id
		vq.k_band = k_band
		vq.word = word
		vq.is_word = is_word
		vq.save()


print VocabQuestion.objects.all()
