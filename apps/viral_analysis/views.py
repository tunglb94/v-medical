from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.authentication.decorators import allowed_users

from .analyzer import analyze_script, suggest_content_ideas
from .models import ViralSubmission

VIRAL_ROLES = ['ADMIN', 'MARKETING', 'CONTENT', 'EDITOR', 'DESIGNER']


@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=VIRAL_ROLES)
def submission_list(request):
    submissions = ViralSubmission.objects.select_related('submitted_by').all()
    if request.user.role != 'ADMIN':
        submissions = submissions.filter(submitted_by=request.user)

    return render(request, 'viral_analysis/submission_list.html', {
        'submissions': submissions[:100],
    })


@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=VIRAL_ROLES)
def submission_create(request):
    if request.method == 'POST':
        platform = request.POST.get('platform')
        content_type = request.POST.get('content_type') or ViralSubmission.ContentType.SCRIPT
        title = request.POST.get('title', '').strip()
        hook = request.POST.get('hook', '').strip()
        script_content = request.POST.get('script_content', '').strip()
        post_caption = request.POST.get('post_caption', '').strip()

        if not platform or not hook or not script_content:
            messages.error(request, "Vui lòng nhập đủ Nền tảng, Hook và Nội dung kịch bản.")
            return render(request, 'viral_analysis/submission_form.html', {
                'platforms': ViralSubmission.Platform.choices,
                'content_types': ViralSubmission.ContentType.choices,
                'form_data': request.POST,
            })

        submission = ViralSubmission.objects.create(
            platform=platform, content_type=content_type, title=title, hook=hook,
            script_content=script_content, post_caption=post_caption,
            submitted_by=request.user,
        )

        try:
            result = analyze_script(
                submission.get_platform_display(), content_type,
                submission.get_content_type_display(), hook, script_content, post_caption
            )
            submission.score = result['score']
            submission.verdict = result['verdict']
            submission.checks = result.get('checks', [])
            submission.strengths = result['strengths']
            submission.weaknesses = result['weaknesses']
            submission.suggestions = result['suggestions']
            submission.rewrite_examples = result.get('rewrite_examples', [])
            submission.production_tips = result.get('production_tips', [])
            submission.platform_fit = result['platform_fit']
            submission.status = ViralSubmission.Status.DONE
        except Exception as e:
            submission.status = ViralSubmission.Status.ERROR
            submission.error_message = str(e)
            messages.error(request, f"Lỗi khi chấm điểm: {e}")

        submission.analyzed_at = timezone.now()
        submission.save()

        return redirect('viral_analysis:submission_detail', submission.id)

    return render(request, 'viral_analysis/submission_form.html', {
        'platforms': ViralSubmission.Platform.choices,
        'content_types': ViralSubmission.ContentType.choices,
    })


@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=VIRAL_ROLES)
def submission_detail(request, submission_id):
    submission = get_object_or_404(ViralSubmission, id=submission_id)
    if request.user.role != 'ADMIN' and submission.submitted_by_id != request.user.id:
        messages.error(request, "Bạn không có quyền xem kịch bản này.")
        return redirect('viral_analysis:submission_list')

    return render(request, 'viral_analysis/submission_detail.html', {
        'submission': submission,
    })


@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=VIRAL_ROLES)
def submission_delete(request, submission_id):
    submission = get_object_or_404(ViralSubmission, id=submission_id)
    if request.user.role != 'ADMIN' and submission.submitted_by_id != request.user.id:
        messages.error(request, "Bạn không có quyền xoá kịch bản này.")
        return redirect('viral_analysis:submission_list')

    if request.method == 'POST':
        submission.delete()
        messages.success(request, "Đã xoá kịch bản.")
        return redirect('viral_analysis:submission_list')

    return redirect('viral_analysis:submission_detail', submission.id)


@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=VIRAL_ROLES)
def idea_suggest(request):
    ideas = None
    niche = ''
    notes = ''

    if request.method == 'POST':
        niche = request.POST.get('niche', '').strip()
        notes = request.POST.get('notes', '').strip()

        if not niche:
            messages.error(request, "Vui lòng nhập ngành/dịch vụ muốn làm content.")
        else:
            try:
                result = suggest_content_ideas(niche, notes)
                ideas = result.get('ideas', [])
            except Exception as e:
                messages.error(request, f"Lỗi khi gợi ý chủ đề: {e}")

    return render(request, 'viral_analysis/idea_suggest.html', {
        'ideas': ideas,
        'niche': niche,
        'notes': notes,
    })
