
from django.conf.urls import url
from . import views

app_name = 'assessment'
urlpatterns = [
	url(r'^$', views.indexView, name = 'index'),
	url(r'^login$', views.loginView, name = 'login'),
	url(r'^logout$', views.logoutView, name = 'logout'),
	url(r'^vocab$', views.vocabView, name = 'vocab'),
	url(r'^vocab_query/(?P<vocab_word>[a-z ]+)/$', views.vocabQueryView, name = 'vocab_query'),
	url(r'^passage$', views.passageView, name = 'passage'),
]
