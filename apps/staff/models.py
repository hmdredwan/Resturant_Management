from django.db import models


class Shift(models.Model):
    staff = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="shifts")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    notes = models.TextField(blank=True)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-start_time"]

    def __str__(self):
        return f"{self.staff} | {self.start_time.strftime('%Y-%m-%d %H:%M')}"
