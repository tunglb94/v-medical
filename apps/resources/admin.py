from django.contrib import admin
from .models import ProductDocument, TrainingQuestion, TrainingChoice, UserTestResult

# Cho phép nhập Đáp án ngay trong giao diện Câu hỏi
class ChoiceInline(admin.TabularInline):
    model = TrainingChoice
    extra = 4  # Mặc định hiện 4 dòng để nhập đáp án A,B,C,D

@admin.register(TrainingQuestion)
class TrainingQuestionAdmin(admin.ModelAdmin):
    list_display = ('content', 'document', 'created_at')
    list_filter = ('document',)
    search_fields = ('content',)
    inlines = [ChoiceInline] # Nhúng form nhập đáp án vào đây

@admin.register(ProductDocument)
class ProductDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'pass_score', 'created_at')
    search_fields = ('title',)
    list_filter = ('category',)

@admin.register(UserTestResult)
class UserTestResultAdmin(admin.ModelAdmin):
    list_display = ('user', 'document', 'score', 'is_passed', 'created_at')
    list_filter = ('is_passed', 'document', 'created_at')
    readonly_fields = ('user', 'document', 'score', 'is_passed', 'correct_answers', 'total_questions')