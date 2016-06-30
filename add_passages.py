#!/usr/bin/env python
import os
import sys

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

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "language_site.settings")
from django.core.management import execute_from_command_line

import django
from assessment.models import Passage
django.setup()


print "Reading passages file."
try:
	fin = open("passages.txt")
	text = fin.read()
except IOError:
	print "Couldn't open passage file!"
	sys.exit(1)
fin.close()

print "Adding passages."


passages = split_by_tag(text, "passage")
for passage in passages:
	id = int(split_by_tag(passage, "id")[0])
	passage_text = split_by_tag(passage, "text")[0].replace("\n","<br />\n")
	name = split_by_tag(passage, "name")[0]

	if id in [p.passage_id for p in Passage.objects.all()]:
		print "Updating passage " + str(id) + " (already in database) . . ."
		p = Passage.objects.get(passage_id = id)
	else:
		print "Adding " + str(id) + " (" + name + ") . . ."
		p = Passage()

	p.passage_id = id
	p.passage_text = unicode(passage_text)
	p.passage_name = unicode(name)

	p.save()


print Passage.objects.all()
