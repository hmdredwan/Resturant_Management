from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Shift
from apps.accounts.models import User
from apps.accounts.views import log_activity, role_required


@login_required
def staff_list(request):
    staff = User.objects.filter(is_active_staff=True).order_by("role", "first_name")
    today = timezone.now().date()
    today_shifts = Shift.objects.filter(start_time__date=today).select_related("staff")
    on_duty_ids = set()
    now = timezone.now()
    for s in today_shifts:
        if s.start_time <= now <= s.end_time and not s.is_completed:
            on_duty_ids.add(s.staff_id)
    return render(request, "staff/list.html", {
        "staff": staff,
        "today_shifts": today_shifts,
        "on_duty_ids": on_duty_ids,
        "role_choices": User.Role.choices,
    })


@login_required
@role_required("owner", "manager")
def shift_list(request):
    shifts = Shift.objects.select_related("staff").order_by("-start_time")[:50]
    staff = User.objects.filter(is_active_staff=True)
    return render(request, "staff/shifts.html", {"shifts": shifts, "staff": staff})


@login_required
@role_required("owner", "manager")
def shift_create(request):
    if request.method == "POST":
        staff_id = request.POST.get("staff_id")
        start = request.POST.get("start_time")
        end = request.POST.get("end_time")
        notes = request.POST.get("notes", "")
        if staff_id and start and end:
            staff = get_object_or_404(User, id=staff_id)
            shift = Shift.objects.create(staff=staff, start_time=start, end_time=end, notes=notes)
            log_activity(request.user, "create", f"Created shift for {staff.username}", "Shift", shift.id, request)
            messages.success(request, "Shift created.")
        return redirect("shift_list")
    return redirect("shift_list")
