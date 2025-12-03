from django.urls import path

from apps.prompts.views import PromptPlaygroundView

app_name = 'prompts'

urlpatterns = [
    path('', PromptPlaygroundView.as_view(), name='playground'),
]
