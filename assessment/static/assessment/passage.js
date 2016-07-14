function validateForm()
{
	var form;
	form = document.getElementById("answerform");
	var val;
	for (i = 0 ; i < form.length ; i ++)
	{
		name = form.elements[i].name;
		if (name.indexOf("pickone") != -1 || name.indexOf("pickmany") != -1 || name.indexOf("table") != -1 || name.indexOf("shortresponse") != -1 || name.indexOf("longresponse") != -1)
		{
			//alert(form.elements[i].value);
		}
	}
	return;
}
