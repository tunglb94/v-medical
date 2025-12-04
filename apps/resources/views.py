from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import ProductDocument, TrainingQuestion, UserTestResult

@login_required(login_url='/auth/login/')
def document_list(request):
    all_docs = ProductDocument.objects.all().order_by('category', 'title')
    grouped_docs = {}
    cat_choices = dict(ProductDocument.CATEGORY_CHOICES)

    for doc in all_docs:
        cat_display = cat_choices.get(doc.category, doc.category)
        if cat_display not in grouped_docs:
            grouped_docs[cat_display] = []
        grouped_docs[cat_display].append(doc)

    return render(request, 'resources/document_list.html', {'grouped_docs': grouped_docs})

@login_required(login_url='/auth/login/')
def document_detail(request, pk):
    doc = get_object_or_404(ProductDocument, pk=pk)
    template_path = 'resources/document_detail.html'
    
    content_template = None
    if doc.template_name:
        content_template = f"resources/content/{doc.template_name}"
        
    context = {
        'doc': doc,
        'content_template': content_template
    }
    return render(request, template_path, context)

# --- MỚI THÊM: HÀM XỬ LÝ BÀI THI ---
@login_required(login_url='/auth/login/')
def training_test(request, pk):
    doc = get_object_or_404(ProductDocument, pk=pk)
    questions = doc.questions.all().prefetch_related('choices')

    if not questions.exists():
        messages.warning(request, "Bài đào tạo này chưa có câu hỏi kiểm tra.")
        return redirect('document_detail', pk=pk)

    if request.method == 'POST':
        total_questions = questions.count()
        correct_count = 0
        
        for q in questions:
            selected_choice_id = request.POST.get(f'question_{q.id}')
            if selected_choice_id:
                is_correct = q.choices.filter(id=selected_choice_id, is_correct=True).exists()
                if is_correct:
                    correct_count += 1
        
        score_percent = int((correct_count / total_questions) * 100) if total_questions > 0 else 0
        is_passed = score_percent >= doc.pass_score
        
        UserTestResult.objects.create(
            user=request.user,
            document=doc,
            score=score_percent,
            is_passed=is_passed,
            correct_answers=correct_count,
            total_questions=total_questions
        )
        
        if is_passed:
            messages.success(request, f"Chúc mừng! Bạn đã ĐẬU với số điểm {score_percent}%.")
        else:
            messages.error(request, f"Bạn chưa đạt. Điểm: {score_percent}%. Cần {doc.pass_score}% để đậu. Hãy ôn lại và thi lại nhé!")
            
        return redirect('document_detail', pk=pk)

    return render(request, 'resources/training_test.html', {
        'doc': doc,
        'questions': questions
    })