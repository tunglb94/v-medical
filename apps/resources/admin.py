from django.contrib import admin
from .models import ProductDocument

@admin.register(ProductDocument)
class ProductDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'updated_at')
    search_fields = ('title', 'content')
    list_filter = ('category',)