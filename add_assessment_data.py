#!/usr/bin/env python
import os
import sys
import django
from django.core.management import execute_from_command_line
from django.utils.encoding import smart_text

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



def add_passage_questions():
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
		id = split_by_tag(question, "id")[0].strip()
		question_set = split_by_tag(question, "set")[0].strip()
		passage = split_by_tag(question, "passage")[0]
		question_type = split_by_tag(question, "question type")[0]
		prompt = split_by_tag(question, "prompt")[0]

		if question_type == "pick one" or question_type == "pick many":
			hint1 = split_by_tag(question, "hint1")
			if len(hint1) == 0:
				hint1 = None
			else:
				hint1 = hint1[0]
			hint2 = split_by_tag(question, "hint2")
			if len(hint2) == 0:
				hint2 = None
			else:
				hint2 = hint2[0]
			answer_choices = ""
			choices = split_by_tag(question, "answer choice")
			for choice in choices:
				answer_choices = answer_choices + "<choice>" + choice + "</choice>"
			correct_answer = split_by_tag(question, "correct answer")[0]
		else:
			hint1 = None
			hint2 = None
			answer_choices = None
			correct_answer = None

		if id in [pq.pq_id for pq in PassageQuestion.objects.all()]:
			print "Updating question " + str(id) + " (already in database) . . ."
			pq = PassageQuestion.objects.get(pq_id=id)
		else:
			print "Adding " + str(id) + " (" + question_type + ") . . ."
			pq = PassageQuestion()

		pq.pq_id = id
		pq.question_set = question_set
		pq.passage = unicode(passage)
		pq.question_type = unicode(question_type)
		pq.prompt = unicode(prompt)
		pq.hint1 = unicode(hint1)
		pq.hint2 = unicode(hint2)
		pq.answer_choices = unicode(answer_choices)
		pq.correct_answer = unicode(correct_answer)

		pq.save()
	return


def add_passages():
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
	return


def add_vocab_hints():
	print "Reading definitions file."
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
		translation = smart_text(fields[1])
		definition = smart_text(fields[2])

		if word in [vh.word for vh in VocabHint.objects.all()]:
			print "Updating " + word + " (already in database) . . ."
			vh = VocabHint.objects.get(word=word)
		else:
			vh = VocabHint()
			print "Adding \'" + word + "\': " + translation + " - " + definition

		vh.word = word
		vh.translation = translation
		vh.definition = definition
		vh.save()

	return


def add_vocab_questions():
	print "Reading vocab questions file."
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
			print "Updating " + word + " (already in database) . . ."
			vq = VocabQuestion.objects.get(item_id=item_id)
		else:

			print "Adding word:  " + str(item_id) + ", " + str(k_band) + ", " + str(word) + ", " + str(is_word)

			vq = VocabQuestion()
		vq.item_id = item_id
		vq.k_band = k_band
		vq.word = word
		vq.is_word = is_word
		vq.save()
	return

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "language_site.settings")
django.setup()
from assessment.models import *

add_vocab_questions()
add_vocab_hints()
add_passages()
add_passage_questions()
