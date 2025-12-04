from django.db import models
from django.conf import settings

class ProductDocument(models.Model):
    CATEGORY_CHOICES = [
        ('MACHINE', 'Máy móc & Công nghệ'),
        ('PROTOCOL', 'Phác đồ điều trị'),
        ('SERVICE', 'Dịch vụ lâm sàng'),
        ('INTERNAL_TRAINING', 'Đào tạo nội bộ'),
    ]

    title = models.CharField(max_length=200, verbose_name="Tên tài liệu")
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='MACHINE')
    image_url = models.URLField(max_length=500, blank=True, null=True, verbose_name="Link Ảnh minh họa")
    
    # Lưu tên file template nội dung (VD: intima.html, marketing_4p.html)
    template_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tên file HTML nội dung")
    
    short_description = models.TextField(verbose_name="Mô tả ngắn", blank=True)
    
    # --- MỚI: ĐIỂM CHUẨN ĐỂ ĐẠT ---
    pass_score = models.IntegerField(default=80, verbose_name="Điểm đạt (%)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Tài liệu đào tạo"
        verbose_name_plural = "Kho Tài liệu"

# --- CÁC MODEL MỚI CHO TÍNH NĂNG THI TRẮC NGHIỆM ---

class TrainingQuestion(models.Model):
    document = models.ForeignKey(ProductDocument, on_delete=models.CASCADE, related_name='questions', verbose_name="Tài liệu")
    content = models.TextField(verbose_name="Nội dung câu hỏi")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.document.title} - {self.content[:50]}..."

    class Meta:
        verbose_name = "Câu hỏi trắc nghiệm"
        verbose_name_plural = "Kho Câu hỏi"

class TrainingChoice(models.Model):
    question = models.ForeignKey(TrainingQuestion, on_delete=models.CASCADE, related_name='choices', verbose_name="Câu hỏi")
    content = models.CharField(max_length=255, verbose_name="Nội dung đáp án")
    is_correct = models.BooleanField(default=False, verbose_name="Là đáp án đúng")

    def __str__(self):
        return self.content

class UserTestResult(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Nhân viên")
    document = models.ForeignKey(ProductDocument, on_delete=models.CASCADE, verbose_name="Bài kiểm tra")
    score = models.IntegerField(verbose_name="Điểm số (0-100)")
    is_passed = models.BooleanField(default=False, verbose_name="Đạt yêu cầu")
    correct_answers = models.IntegerField(default=0, verbose_name="Số câu đúng")
    total_questions = models.IntegerField(default=0, verbose_name="Tổng số câu")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày thi")

    def __str__(self):
        return f"{self.user.username} - {self.document.title} - {self.score}%"

    class Meta:
        verbose_name = "Kết quả bài thi"
        verbose_name_plural = "Lịch sử thi"