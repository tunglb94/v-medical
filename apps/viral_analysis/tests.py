from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from apps.viral_analysis.models import ViralSubmission

User = get_user_model()


class ViralAnalysisViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='marketer1', password='testpass123', role='MARKETING')
        self.client = Client()
        self.client.force_login(self.user)

    def test_list_view_empty(self):
        resp = self.client.get('/viral-analysis/')
        self.assertEqual(resp.status_code, 200)

    def test_form_view_get(self):
        resp = self.client.get('/viral-analysis/new/')
        self.assertEqual(resp.status_code, 200)

    def test_detail_view_done(self):
        sub = ViralSubmission.objects.create(
            platform='TIKTOK', title='Test render',
            hook='Test hook', script_content='Test script',
            post_caption='Test caption', submitted_by=self.user,
            status='DONE', score=55, verdict='Tam on.',
            checks=[
                {"criterion": "Suc manh Hook", "status": "ok", "sub_score": 60, "assessment": "Tam on"},
                {"criterion": "CTA", "status": "bad", "sub_score": 20, "assessment": "Khong co CTA"},
            ],
            strengths=['A', 'B'], weaknesses=['C'], suggestions=['D', 'E'],
            production_tips=[
                {"aspect": "Visual hook", "suggestion": "Mo dau bang hinh anh ket qua"},
                {"aspect": "Nhac nen", "suggestion": "Dung trending sound nhe"},
            ],
            platform_fit='Kha phu hop.'
        )
        resp = self.client.get(f'/viral-analysis/{sub.id}/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, '55')

    def test_detail_view_error_status(self):
        sub = ViralSubmission.objects.create(
            platform='YOUTUBE', title='Err case',
            hook='h', script_content='s', submitted_by=self.user,
            status='ERROR', error_message='API timeout',
        )
        resp = self.client.get(f'/viral-analysis/{sub.id}/')
        self.assertEqual(resp.status_code, 200)

    def test_other_user_cannot_view(self):
        other = User.objects.create_user(username='marketer2', password='testpass123', role='MARKETING')
        sub = ViralSubmission.objects.create(
            platform='FACEBOOK', hook='h', script_content='s', submitted_by=other, status='PENDING',
        )
        resp = self.client.get(f'/viral-analysis/{sub.id}/')
        # non-owner, non-admin should be redirected away
        self.assertEqual(resp.status_code, 302)
