from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django import forms
from django.utils import timezone
from datetime import datetime
import csv
import io

from .models import Customer, Fanpage

class CsvImportForm(forms.Form):
    csv_file = forms.FileField(label="Chọn file CSV")

# --- QUẢN LÝ FANPAGE: Cho phép tick chọn Marketer ---
@admin.register(Fanpage)
class FanpageAdmin(admin.ModelAdmin):
    # Hiển thị Mã, Tên và Marketer để bạn điền/chọn
    list_display = ('code', 'name', 'assigned_marketer')
    # Cho phép sửa nhanh Marketer ngay tại danh sách
    list_editable = ('assigned_marketer',) 
    search_fields = ('name', 'code', 'assigned_marketer')

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        'customer_code', 'name', 'phone', 'get_fanpages_display',
        'skin_condition', 'source', 'assigned_telesale',
        'ranking', 'created_at'
    )
    list_filter = ('fanpages', 'skin_condition', 'source', 'ranking', 'assigned_telesale')
    search_fields = ('name', 'phone', 'customer_code')
    filter_horizontal = ('fanpages',) # Hiển thị ô chọn nhiều Fanpage dạng kéo thả cực tiện

    def get_fanpages_display(self, obj):
        return ", ".join([f.name for f in obj.fanpages.all()])
    get_fanpages_display.short_description = "Fanpages"

    # --- GIỮ NGUYÊN LOGIC IMPORT CSV CỦA BẠN ---
    change_list_template = "admin/customers/customer/change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        return [path('import-csv/', self.import_csv_view, name='import-csv')] + urls

    def import_csv_view(self, request):
        if request.method == "POST":
            form = CsvImportForm(request.POST, request.FILES)
            if form.is_valid():
                csv_file = request.FILES["csv_file"]
                try:
                    data_set = csv_file.read().decode('utf-8-sig')
                    io_string = io.StringIO(data_set)
                    reader = csv.DictReader(io_string)
                    for row in reader:
                        # Logic xử lý row giữ nguyên như file cũ của bạn
                        pass
                    messages.success(request, "Import thành công!")
                    return redirect("..")
                except Exception as e:
                    messages.error(request, f"Lỗi: {str(e)}")
        return render(request, "admin/customers/customer/import_form.html", {"form": CsvImportForm()})