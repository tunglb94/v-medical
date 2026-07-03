import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('sales', '0003_order_order_date_index'),
        ('customers', '0007_customer_customer_code_customer_fanpage'),
        ('service_calendar', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PlannedSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_type', models.CharField(choices=[('MAIN', 'Buổi chính'), ('BONUS', 'Buổi tặng kèm')], default='MAIN', max_length=10, verbose_name='Loại buổi')),
                ('session_number', models.PositiveIntegerField(default=1, verbose_name='Buổi số')),
                ('total_in_group', models.PositiveIntegerField(default=1, verbose_name='Tổng buổi cùng loại')),
                ('status', models.CharField(choices=[('PENDING', 'Chưa đặt lịch'), ('SCHEDULED', 'Đã đặt lịch'), ('DONE', 'Đã hoàn thành'), ('CANCELLED', 'Đã huỷ')], default='PENDING', max_length=10, verbose_name='Trạng thái')),
                ('scheduled_date', models.DateTimeField(blank=True, null=True, verbose_name='Ngày giờ hẹn')),
                ('note', models.TextField(blank=True, verbose_name='Ghi chú')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='planned_sessions', to='sales.order', verbose_name='Đơn hàng')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='planned_sessions', to='customers.customer', verbose_name='Khách hàng')),
                ('service', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='sales.service', verbose_name='Dịch vụ')),
                ('assigned_doctor', models.ForeignKey(blank=True, limit_choices_to={'role': 'DOCTOR'}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='planned_sessions_as_doctor', to=settings.AUTH_USER_MODEL, verbose_name='Bác sĩ phụ trách')),
                ('assigned_technician', models.ForeignKey(blank=True, limit_choices_to={'role': 'TECHNICIAN'}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='planned_sessions_as_tech', to=settings.AUTH_USER_MODEL, verbose_name='KTV phụ trách')),
                ('completed_log', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='service_calendar.treatmentsession', verbose_name='Bản ghi tính hoa hồng')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Buổi điều trị đã lên kế hoạch',
                'verbose_name_plural': 'Kế hoạch điều trị',
                'ordering': ['scheduled_date', 'session_number'],
            },
        ),
    ]
