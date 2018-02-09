from django.test import TestCase

from .models import VocabQuestion, Student, VocabHint, PassageQuestion

class PassageQuestionMethodTests(TestCase):
	def test_pick_one(self):
		print "Pick one test."
		pq = PassageQuestion()
		pq.pq_id = 0
		pq.question_type = "pick one"
		pq.prompt = "Check one."
		pq.answer_choices = "<choice>A</choice><choice>B</choice>"
		self.assertEqual(len(pq.get_answer_choices()), 2)
		self.assertEqual(pq.get_row_headings(), None)
		self.assertEqual(pq.get_col_headings(), None)
		return
		
	def test_pick_many(self):
		print "Pick many test."
		pq = PassageQuestion()
		pq.pq_id = 0
		pq.question_type = "pick many"
		pq.prompt = "Check all that apply."
		pq.answer_choices = "<choice>A</choice><choice>B</choice>"
		self.assertEqual(len(pq.get_answer_choices()), 2)
		self.assertEqual(pq.get_row_headings(), None)
		self.assertEqual(pq.get_col_headings(), None)
		return

	def test_table(self):
		print "Table test."
		pq = PassageQuestion()
		pq.pq_id = 0
		pq.question_type = "table"
		pq.prompt = "<row>Rhymes with tea</row><row>Rhymes with dew</row><col>after S</col><col>Before S</col>"
		pq.answer_choices = "<choice>Q</choice><choice>U</choice><choice>V</choice><choice>B</choice>"
		self.assertEqual(len(pq.get_answer_choices()), 4)
		self.assertEqual(len(pq.get_row_headings()), 2)
		self.assertEqual(len(pq.get_col_headings()), 2)
		return

	def test_short_response(self):
		print "Short response test."
		pq = PassageQuestion()
		pq.pq_id = 0
		pq.question_type = "short response"
		pq.prompt = "Write a short response."
		pq.answer_choices = ""
		self.assertEqual(pq.get_answer_choices(), None)
		self.assertEqual(pq.get_row_headings(), None)
		self.assertEqual(pq.get_col_headings(), None)
		return

	def test_long_response(self):
		print "Long response test."
		pq = PassageQuestion()
		pq.pq_id = 0
		pq.question_type = "long response"
		pq.prompt = "Write a long response."
		pq.answer_choices = ""
		self.assertEqual(pq.get_answer_choices(), None)
		self.assertEqual(pq.get_row_headings(), None)
		self.assertEqual(pq.get_col_headings(), None)
		return

class StudentMethodTests(TestCase):
	def test_add_and_fetch_passage_results(self):
		print "add and fetch test."
		pq1 = PassageQuestion(pq_id = 0)
		pq2 = PassageQuestion(pq_id = 1)
		pq3 = PassageQuestion(pq_id = 2)
		#unfinished
		return

