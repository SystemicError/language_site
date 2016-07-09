#!/usr/bin/env python
import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "language_site.settings")
from django.core.management import execute_from_command_line


import django
from django.utils.encoding import smart_text
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
	fields = line.split("\t")
	word = smart_text(fields[0])

	if word in [vh.word for vh in VocabHint.objects.all()]:
		print "Updating " + word + " (already in database) . . ."
		vh = VocabHint.objects.get(word=word)
	else:
		vh = VocabHint()
		print "Adding \'" + word + "\': " + translation + " - " + definition

	translation = smart_text(fields[1])
	definition = smart_text(fields[2])


	vh.word = word
	vh.translation = translation
	vh.definition = definition
	vh.save()


print VocabHint.objects.all()
