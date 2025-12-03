from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import ProductDocument

@login_required(login_url='/auth/login/')
def document_list(request):
    docs = ProductDocument.objects.all().order_by('category', 'title')
    return render(request, 'resources/document_list.html', {'docs': docs})

@login_required(login_url='/auth/login/')
def document_detail(request, pk):
    doc = get_object_or_404(ProductDocument, pk=pk)
    
    # Nếu có file template riêng thì dùng, không thì dùng template mặc định
    template_path = 'resources/document_detail.html' # Mặc định
    
    # Truyền tên file nội dung vào context để include
    context = {
        'doc': doc,
        'content_template': f"resources/content/{doc.template_name}" if doc.template_name else None
    }
    return render(request, template_path, context)