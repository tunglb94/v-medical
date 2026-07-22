from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from apps.viral_analysis.analyzer import CHECK_WEIGHTS, compute_score
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

    def test_owner_can_delete(self):
        sub = ViralSubmission.objects.create(
            platform='TIKTOK', hook='h', script_content='s', submitted_by=self.user, status='PENDING',
        )
        resp = self.client.post(f'/viral-analysis/{sub.id}/delete/')
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(ViralSubmission.objects.filter(id=sub.id).exists())

    def test_other_user_cannot_delete(self):
        other = User.objects.create_user(username='marketer3', password='testpass123', role='MARKETING')
        sub = ViralSubmission.objects.create(
            platform='FACEBOOK', hook='h', script_content='s', submitted_by=other, status='PENDING',
        )
        resp = self.client.post(f'/viral-analysis/{sub.id}/delete/')
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(ViralSubmission.objects.filter(id=sub.id).exists())


class ComputeScoreTests(TestCase):
    def test_weights_sum_to_100(self):
        self.assertEqual(sum(CHECK_WEIGHTS.values()), 100)

    def test_weighted_average(self):
        checks = [{"criterion": name, "sub_score": 100} for name in CHECK_WEIGHTS]
        self.assertEqual(compute_score(checks), 100)

        checks = [{"criterion": name, "sub_score": 0} for name in CHECK_WEIGHTS]
        self.assertEqual(compute_score(checks), 0)

    def test_ignores_unknown_criterion(self):
        checks = [
            {"criterion": "Sức mạnh Hook (0-3s)", "sub_score": 80},
            {"criterion": "Ten khong khop", "sub_score": 0},
        ]
        # Chỉ tính theo trọng số của tiêu chí khớp tên -> phải bằng đúng sub_score đó
        self.assertEqual(compute_score(checks), 80)

    def test_empty_checks_returns_zero(self):
        self.assertEqual(compute_score([]), 0)
