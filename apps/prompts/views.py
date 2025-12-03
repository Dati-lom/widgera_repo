from itertools import zip_longest
from typing import Dict, List

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from apps.prompts.models import PromptExecution
from apps.prompts.services import (
    LLMServiceError,
    image_handler,
    llm_service,
)


class PromptPlaygroundView(LoginRequiredMixin, TemplateView):
    template_name = 'prompts/prompt_playground.html'
    login_url = reverse_lazy('users_web:login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault('prompt_text', '')
        context.setdefault('field_rows', self._default_fields())
        context['history'] = self._fetch_history(self.request.user)
        return context

    def post(self, request, *args, **kwargs):
        prompt_text = request.POST.get('prompt_text', '').strip()
        field_rows = self._parse_fields(request)
        context = self.get_context_data()
        context.update(
            {
                'prompt_text': prompt_text,
                'field_rows': field_rows or self._default_fields(),
            }
        )
        context['history'] = self._fetch_history(request.user)

        if not prompt_text:
            context['error_message'] = 'Prompt text is required.'
            return self.render_to_response(context)

        image_result = None
        image_file = request.FILES.get('image')
        if image_file:
            try:
                image_result = image_handler.handle_upload(request.user, image_file)
                image_obj = image_result.image
                image_url = getattr(image_obj, 'image_url', None)
                if not image_url and hasattr(image_obj, 'file') and image_obj.file:
                    image_url = image_obj.file.url
                context['image_preview_url'] = image_url
                if image_result.is_duplicate:
                    context['image_notice'] = 'Existing upload reused for this request.'
            except ValidationError as exc:
                context['error_message'] = str(exc)
                return self.render_to_response(context)
            except Exception as exc:  # noqa: BLE001
                context['error_message'] = f"Image upload failed: {exc}"
                return self.render_to_response(context)
        else:
            context['image_preview_url'] = None

        try:
            llm_response = llm_service.generate_structured_response(
                prompt_text=prompt_text,
                fields=context['field_rows'],
                image_url=context.get('image_preview_url'),
            )
        except (ValueError, LLMServiceError) as exc:
            context['error_message'] = str(exc)
            return self.render_to_response(context)

        PromptExecution.objects.create(
            user=request.user,
            prompt_text=prompt_text,
            structured_fields=context['field_rows'],
            result_data=llm_response.structured_data,
            provider='openai',
            model_name=llm_response.model,
            status=PromptExecution.Status.COMPLETED,
            image=image_result.image if image_result else None,
        )

        context['structured_output'] = llm_response.structured_data
        context['llm_usage'] = llm_response.usage
        return self.render_to_response(context)

    def _parse_fields(self, request) -> List[Dict[str, str]]:
        names = request.POST.getlist('field_names[]')
        types = request.POST.getlist('field_types[]')
        rows: List[Dict[str, str]] = []
        for name, field_type in zip_longest(names, types, fillvalue='string'):
            clean_name = (name or '').strip()
            if not clean_name:
                continue
            clean_type = (field_type or 'string').lower()
            if clean_type not in {'string', 'number'}:
                clean_type = 'string'
            rows.append({'name': clean_name, 'field_type': clean_type})
        return rows

    def _default_fields(self) -> List[Dict[str, str]]:
        return [
            {'name': 'inventorFullName', 'field_type': 'string'},
            {'name': 'inventorBirthYear', 'field_type': 'number'},
            {'name': 'numberOnTheShirt', 'field_type': 'number'},
        ]

    def _fetch_history(self, user, limit: int = 5):
        if not user.is_authenticated:
            return []
        qs = (
            PromptExecution.objects.select_related('image')
            .filter(user=user)
            .order_by('-created_at')[:limit]
        )
        history = []
        for execution in qs:
            image_url = None
            if execution.image:
                image_url = execution.image.image_url or (
                    execution.image.file.url if execution.image.file else None
                )
            history.append(
                {
                    'id': execution.id,
                    'prompt_text': execution.prompt_text,
                    'result_data': execution.result_data,
                    'created_at': execution.created_at,
                    'model_name': execution.model_name,
                    'image_url': image_url,
                }
            )
        return history
