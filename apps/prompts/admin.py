from django.contrib import admin

from .models import PromptSchema, SchemaField, UploadedImage, PromptExecution


class SchemaFieldInline(admin.TabularInline):
    model = SchemaField
    extra = 0


@admin.register(PromptSchema)
class PromptSchemaAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'user__username')
    inlines = [SchemaFieldInline]


@admin.register(UploadedImage)
class UploadedImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'checksum', 'created_at')
    search_fields = ('user__username', 'checksum')


@admin.register(PromptExecution)
class PromptExecutionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'provider', 'model_name', 'created_at')
    list_filter = ('status', 'provider')
    search_fields = ('user__username', 'prompt_text')
    autocomplete_fields = ('schema', 'image')
