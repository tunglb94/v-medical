from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import ProductDocument

@login_required(login_url='/auth/login/')
def document_list(request):
    # Lấy tất cả tài liệu, ai cũng xem được
    docs = ProductDocument.objects.all().order_by('category', 'title')
    
    # Nhóm theo danh mục để hiển thị cho đẹp
    grouped_docs = {}
    for doc in docs:
        cat_display = doc.get_category_display()
        if cat_display not in grouped_docs:
            grouped_docs[cat_display] = []
        grouped_docs[cat_display].append(doc)

    return render(request, 'resources/document_list.html', {'grouped_docs': grouped_docs})

@login_required(login_url='/auth/login/')
def document_detail(request, pk):
    doc = get_object_or_404(ProductDocument, pk=pk)
    return render(request, 'resources/document_detail.html', {'doc': doc})