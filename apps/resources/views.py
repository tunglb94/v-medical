from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import ProductDocument

@login_required(login_url='/auth/login/')
def document_list(request):
    # 1. Lấy tất cả tài liệu, sắp xếp theo danh mục
    all_docs = ProductDocument.objects.all().order_by('category', 'title')
    
    # 2. Nhóm tài liệu theo danh mục (để khớp với template)
    grouped_docs = {}
    
    # Lấy dictionary để hiển thị tên danh mục đẹp hơn (VD: 'MACHINE' -> 'Máy móc & Công nghệ')
    cat_choices = dict(ProductDocument.CATEGORY_CHOICES)

    for doc in all_docs:
        # Lấy tên hiển thị của danh mục
        cat_display = cat_choices.get(doc.category, doc.category)
        
        if cat_display not in grouped_docs:
            grouped_docs[cat_display] = []
        grouped_docs[cat_display].append(doc)

    # 3. Gửi biến 'grouped_docs' sang template
    return render(request, 'resources/document_list.html', {'grouped_docs': grouped_docs})

@login_required(login_url='/auth/login/')
def document_detail(request, pk):
    doc = get_object_or_404(ProductDocument, pk=pk)
    
    # Logic chọn file template nội dung
    template_path = 'resources/document_detail.html' # Mặc định
    
    # Truyền tên file nội dung vào context để include
    content_template = None
    if doc.template_name:
        content_template = f"resources/content/{doc.template_name}"
        
    context = {
        'doc': doc,
        'content_template': content_template
    }
    return render(request, template_path, context)