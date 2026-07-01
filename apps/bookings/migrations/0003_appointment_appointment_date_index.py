from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Chỉ thêm index cho appointment_date để tối ưu tốc độ lọc báo cáo doanh thu.
    Viết tay (không dùng makemigrations) vì models.py hiện có field note/service
    trên Appointment (thêm ở commit cb7330b) chưa từng được migrate - chạy
    autodetector sẽ gộp cả phần lệch đó vào, rất rủi ro cho production.
    """

    dependencies = [
        ('bookings', '0002_appointment_assigned_technician'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='appointment',
            index=models.Index(fields=['appointment_date'], name='bookings_appt_date_idx'),
        ),
    ]
