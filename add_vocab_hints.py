#!/usr/bin/env python
import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "language_site.settings")
from django.core.management import execute_from_command_line


import django
from assessment.models import VocabHint
django.setup()


print "Reading text file."
try:
	fin = open("definitions.txt")
	lines = fin.readlines()
except IOError:
	print "Couldn't open vocab file!"
	sys.exit(1)
fin.close()

print "Adding words."

for line in lines:
	fields = line.split()
	word = fields[0]

	if word in [vh.word for vh in VocabHint.objects.all()]:
		print "Skipping " + word + " (already in database) . . ."
	else:
		definition = ""
		for x in fields[1:]:
			definition = definition + x + " "

		print "Adding \'" + word + "\': " + definition

		vh = VocabHint()
		vh.word = word
		vh.definition = definition
		vh.save()


print VocabHint.objects.all()
