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
from assessment.models import PassageQuestion
django.setup()


print "Reading passage questions file."
try:
	fin = open("passage_questions.txt")
	text = fin.read()
except IOError:
	print "Couldn't open passage questions file!"
	sys.exit(1)
fin.close()

print "Adding passage questions."


questions = split_by_tag(text, "question")
for question in questions:
	id = int(split_by_tag(question, "id")[0])
	passage = split_by_tag(question, "passage")[0]
	question_type = split_by_tag(question, "question type")[0]
	prompt = split_by_tag(question, "prompt")[0]

	if question_type == "pick one" or question_type == "pick many" or question_type == "table":
		hint1 = split_by_tag(question, "hint1")[0]
		hint2 = split_by_tag(question, "hint2")[0]
		answer_choices = ""
		choices = split_by_tag(question, "answer choice")
		for choice in choices:
			answer_choices = answer_choices + "<choice>" + choice + "</choice>"
		correct_answer = split_by_tag(question, "correct answer")[0]
	else:
		print "nones"
		hint1 = None
		hint2 = None
		answer_choices = None
		correct_answer = None

	if id in [pq.pq_id for pq in PassageQuestion.objects.all()]:
		print "Skipping question " + str(id) + " (already in database) . . ."
	else:
		print "Adding " + str(id) + " (" + question_type + ") . . ."

		pq = PassageQuestion()
		pq.pq_id = id
		pq.passage = unicode(passage)
		pq.question_type = unicode(question_type)
		pq.prompt = unicode(prompt)
		pq.hint1 = unicode(hint1)
		pq.hint2 = unicode(hint2)
		pq.answer_choices = unicode(answer_choices)
		pq.correct_answer = unicode(correct_answer)

		pq.save()


print PassageQuestion.objects.all()
