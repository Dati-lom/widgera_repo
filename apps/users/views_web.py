from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.views.generic import FormView


class BootstrapFormMixin:
    field_class = 'form-control'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field in form.fields.values():
            existing = field.widget.attrs.get('class', '')
            classes = f"{existing} {self.field_class}".strip()
            field.widget.attrs['class'] = classes
        return form


class UserSignupView(BootstrapFormMixin, FormView):
    template_name = 'users/signup.html'
    form_class = UserCreationForm
    success_url = reverse_lazy('prompts:playground')

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return super().form_valid(form)


class UserLoginView(BootstrapFormMixin, LoginView):
    template_name = 'users/login.html'
    authentication_form = AuthenticationForm
    redirect_authenticated_user = True
    next_page = reverse_lazy('prompts:playground')
