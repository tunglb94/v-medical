import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    """
    App service_calendar chưa từng có migration nào được commit (dù bảng đã tồn
    tại thật trên production - model đang chạy). File này ghi lại đúng trạng thái
    hiện tại của models.py, KHÔNG thay đổi field nào, chỉ để có 1 điểm neo migration
    hợp lệ cho app khác (clinical_portal) tham chiếu FK tới TreatmentSession.
    Trên production cần chạy `migrate service_calendar --fake` vì bảng đã có sẵn.
    """

    initial = True

    dependencies = [
        ('customers', '0001_initial'),
        ('sales', '0002_service_alter_order_total_amount_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TreatmentSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_date', models.DateTimeField(auto_now_add=True, verbose_name='Thời gian làm')),
                ('note', models.TextField(blank=True, verbose_name='Ghi chú buổi làm')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='customers.customer', verbose_name='Khách hàng')),
                ('service', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='sales.service', verbose_name='Dịch vụ thực hiện')),
                ('order', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='sales.order', verbose_name='Thuộc đơn hàng')),
                ('technician', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sessions_as_tech', to=settings.AUTH_USER_MODEL, verbose_name='KTV chính')),
                ('doctor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sessions_as_doctor', to=settings.AUTH_USER_MODEL, verbose_name='Bác sĩ phụ trách')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Buổi điều trị (Tour)',
                'verbose_name_plural': 'Lịch sử Tour KTV',
                'ordering': ['-session_date'],
            },
        ),
        migrations.CreateModel(
            name='ReminderLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('customer_phone_backup', models.CharField(blank=True, max_length=20)),
                ('reminder_time', models.DateTimeField()),
                ('content', models.TextField()),
                ('status', models.CharField(default='PENDING', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('customer', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='customers.customer')),
                ('assigned_staff', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_reminders', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
