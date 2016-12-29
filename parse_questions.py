path = "questionsILP.txt"

fin = open(path, "r")
lines = [x for x in fin.readlines() if len(x) > 0 and x[0] != "#"]
fin.close()


passage_questions = []
for line in lines:
	line = line.strip()
	fields = [x for x in line.split("\t") if x != "" and x != "\n"]
	question_id = fields[0]
	question_prompt = fields[1]
	question_type = fields[2]
	
	print question_prompt
	print question_type

	question = {}
	question["id"] = question_id
	question["prompt"] = question_prompt
	question["type"] = question_type

	if question_type != "long response" and question_type != "short response":
		# get answer choices
		correct_answer = [x for x in fields[3:] if x.find("(any)") != -1 or x.find("option") != -1][0]
		answer_index = fields.index(correct_answer)
		answer_choices = fields[3:answer_index]
		print answer_choices
		question["answer_choices"] = answer_choices

		print correct_answer

		if len(fields) > answer_index + 1:
			hint1 = fields[answer_index + 1]
			question["hint1"] = hint1
		if len(fields) > answer_index + 2:
			hint2 = fields[answer_index + 2]
			question["hint2"] = hint2

		question["answer_choices"] = answer_choices
		question["correct_answer"] = correct_answer

	passage_questions.append(question)

#print passage_questions

fout = open("questions_formatted.txt", "w")

for pq in passage_questions:
	fout.write("<question>\n\t<id>")
	fout.write(str(pq["id"]))
	fout.write("</id>\n\t<passage>easy</passage>\n\t<question type>")
	fout.write(pq["type"])
	fout.write("</question type>\n\t<prompt>")
	fout.write(pq["prompt"])
	fout.write("</prompt>\n")

	if "hint1" in pq.keys():
		fout.write("\t<hint1>" + pq["hint1"] + "</hint1>\n")
	if "hint2" in pq.keys():
		fout.write("\t<hint2>" + pq["hint2"] + "</hint2>\n")

	if "answer_choices" in pq.keys():
		for choice in pq["answer_choices"]:
			fout.write("\t<answer choice>" + choice + "</answer choice>\n")

	if "correct_answer" in pq.keys():
		fout.write("\t<correct answer>" + pq["correct_answer"] + "</correct answer>\n")

	fout.write("</question>\n\n")

fout.close()
