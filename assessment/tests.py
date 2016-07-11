from django.test import TestCase

from .models import *

class PassageQuestionMethodTests(TestCase):
	def test_pick_one(self):
		print "Pick one test."
		pq = PassageQuestion()
		pq.pq_id = 0
		pq.question_type = "pick one"
		pq.prompt = "Check one."
		pq.answer_choices = "<choice>A</choice><choice>B</choice>"
		pq.correct_answer = "0"
		pq.hint1 = "No . . ."
		pq.hint1 = "Still no . . ."
		self.assertEqual(len(pq.get_answer_choices()), 2)
		self.assertEqual(pq.get_row_headings(), None)
		self.assertEqual(pq.get_col_headings(), None)
		self.assertEqual(pq.get_correct_answer(), 0)
		return
		
	def test_pick_many(self):
		print "Pick many test."
		pq = PassageQuestion()
		pq.pq_id = 0
		pq.question_type = "pick many"
		pq.prompt = "Check all that apply."
		pq.answer_choices = "<choice>A</choice><choice>B</choice>"
		pq.correct_answer = "0 1"
		pq.hint1 = "No . . ."
		pq.hint1 = "Still no . . ."
		self.assertEqual(len(pq.get_answer_choices()), 2)
		self.assertEqual(pq.get_row_headings(), None)
		self.assertEqual(pq.get_col_headings(), None)
		self.assertEqual(pq.get_correct_answer(), (0, 1))
		return

	def test_table(self):
		print "Table test."
		pq = PassageQuestion()
		pq.pq_id = 0
		pq.question_type = "table"
		pq.prompt = "<row>Rhymes with tea</row><row>Rhymes with dew</row><col>after S</col><col>Before S</col>"
		pq.answer_choices = "<choice>Q</choice><choice>U</choice><choice>V</choice><choice>B</choice>"
		pq.correct_answer = "2 3 1 0"
		pq.hint1 = "No . . ."
		pq.hint1 = "Still no . . ."
		self.assertEqual(len(pq.get_answer_choices()), 4)
		self.assertEqual(len(pq.get_row_headings()), 2)
		self.assertEqual(len(pq.get_col_headings()), 2)
		self.assertEqual(pq.get_correct_answer(), (2, 3, 1, 0))
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
		self.assertEqual(pq.get_correct_answer(), None)
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
		self.assertEqual(pq.get_correct_answer(), None)
		return

class StudentMethodTests(TestCase):
	def test_take_vocab_quiz(self):
		print "VocabQuizTest"
		st = Student()
		for i in range(150):
			vq = VocabQuestion()
			vq.item_id = i
			vq.k_band = i/30 + 1
			vq.word = "word" + str(i)
			vq.is_word = (i%2 == 0)
			vq.save()
			st.add_vocab_result(vq, True)
		st.assign_passage()
		if st.vocab_score(2) >= .85:
			self.assertEqual(st.passage_assigned, "hard")
		else:
			self.assertEqual(st.passage_assigned, "easy")

		
		return

	def test_vocab_queries(self):
		print "Vocab Queries:"
		vh = VocabHint()
		vh.word = "water"
		vh.translation = "agua"
		vh.definition = "H20"
		vh.save()
		vh2 = VocabHint()
		vh2.word = "whirlpool"
		vh2.translation = "remolino"
		vh2.definition = "a kind of washing machine"
		vh2.save()
		st = Student()
		st.add_vocab_query(vh)
		print "vqc"
		print st.vocab_query_counts
		st.add_vocab_query(vh)
		print st.vocab_query_counts
		st.add_vocab_query(vh2)
		print st.vocab_query_counts
		queries = st.get_vocab_words_queried()
		self.assertEqual(queries, {"water": 2, "whirlpool": 1})
		return
