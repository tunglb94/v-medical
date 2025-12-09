from django.core.management.base import BaseCommand
from django.conf import settings
import os
import shutil
import datetime
import zipfile
import glob

class Command(BaseCommand):
    help = 'Hệ thống tự động Backup Database và Media files'

    def handle(self, *args, **kwargs):
        # 1. Cấu hình thư mục lưu backup (Tạo folder 'backups' ở thư mục gốc)
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
            self.stdout.write(self.style.WARNING(f"Đã tạo thư mục backup: {backup_dir}"))

        timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        self.stdout.write(f"--- Bắt đầu Backup: {timestamp} ---")

        # 2. Backup Database (SQLite)
        db_file = os.path.join(settings.BASE_DIR, 'db.sqlite3')
        if os.path.exists(db_file):
            backup_db_name = f"db_{timestamp}.sqlite3"
            dest_db_path = os.path.join(backup_dir, backup_db_name)
            shutil.copy2(db_file, dest_db_path)
            self.stdout.write(self.style.SUCCESS(f"✅ Đã backup Database: {backup_db_name}"))
        else:
            self.stdout.write(self.style.ERROR("❌ Không tìm thấy file db.sqlite3"))

        # 3. Backup Media (Nén Zip toàn bộ thư mục ảnh)
        media_root = settings.MEDIA_ROOT
        if os.path.exists(media_root):
            backup_media_name = f"media_{timestamp}.zip"
            dest_media_path = os.path.join(backup_dir, backup_media_name)
            
            try:
                with zipfile.ZipFile(dest_media_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(media_root):
                        for file in files:
                            file_path = os.path.join(root, file)
                            # Lưu đường dẫn tương đối để khi giải nén không bị lỗi
                            arcname = os.path.relpath(file_path, media_root)
                            zipf.write(file_path, arcname)
                self.stdout.write(self.style.SUCCESS(f"✅ Đã backup Media: {backup_media_name}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Lỗi backup Media: {str(e)}"))

        # 4. Dọn dẹp bản backup cũ (Giữ lại 30 bản gần nhất)
        self.cleanup_old_backups(backup_dir, 'db_*.sqlite3', 30)
        self.cleanup_old_backups(backup_dir, 'media_*.zip', 30)

    def cleanup_old_backups(self, folder, pattern, keep_count):
        """Xóa các file cũ, chỉ giữ lại số lượng keep_count mới nhất"""
        files = glob.glob(os.path.join(folder, pattern))
        # Sắp xếp theo thời gian sửa đổi (mới nhất cuối cùng)
        files.sort(key=os.path.getmtime)
        
        if len(files) > keep_count:
            files_to_delete = files[:-keep_count] # Lấy danh sách các file thừa
            for f in files_to_delete:
                try:
                    os.remove(f)
                    self.stdout.write(self.style.WARNING(f"🗑️ Đã xóa backup cũ: {os.path.basename(f)}"))
                except OSError as e:
                    self.stdout.write(self.style.ERROR(f"Lỗi xóa file {f}: {e}"))