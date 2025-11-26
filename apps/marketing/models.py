from django.db import models

class DailyCampaignStat(models.Model):
    report_date = models.DateField(unique=True, verbose_name="Ngày báo cáo")
    
    # 1. Chi phí & Đầu vào
    spend_amount = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name="Ngân sách tiêu (VNĐ)")
    
    # 2. Tương tác
    comments = models.IntegerField(default=0, verbose_name="Số Comment")
    inboxes = models.IntegerField(default=0, verbose_name="Số Inbox")
    
    # 3. Kết quả chuyển đổi
    leads = models.IntegerField(default=0, verbose_name="Số điện thoại (Leads)")
    appointments = models.IntegerField(default=0, verbose_name="Số lịch hẹn")
    
    created_at = models.DateTimeField(auto_now_add=True)

    # --- Các hàm tính toán tự động ---
    @property
    def total_interactions(self):
        return self.comments + self.inboxes

    @property
    def cost_per_lead(self):
        """Giá mỗi số điện thoại (CPL)"""
        if self.leads > 0:
            return self.spend_amount / self.leads
        return 0

    @property
    def cost_per_appointment(self):
        """Giá mỗi lịch hẹn (CPA) - MỚI THÊM"""
        if self.appointments > 0:
            return self.spend_amount / self.appointments
        return 0

    @property
    def conversion_rate_lead(self):
        """Tỷ lệ ra số: SĐT / (Comment + Inbox)"""
        total = self.total_interactions
        if total > 0:
            return (self.leads / total) * 100
        return 0

    @property
    def conversion_rate_appt(self):
        """Tỷ lệ chốt hẹn: Hẹn / SĐT"""
        if self.leads > 0:
            return (self.appointments / self.leads) * 100
        return 0

    def __str__(self):
        return f"Báo cáo ngày {self.report_date}"

    class Meta:
        verbose_name = "Báo cáo Marketing"
        verbose_name_plural = "Báo cáo Marketing"
        ordering = ['-report_date']