from django.db import models


class KitchenTicket(models.Model):
    """
    Optional: Separate kitchen ticket if you want more control.
    For simplicity we mostly use OrderItem status.
    """
    order = models.ForeignKey("orders.Order", on_delete=models.CASCADE, related_name="kitchen_tickets")
    order_item = models.ForeignKey("orders.OrderItem", on_delete=models.CASCADE, related_name="tickets")
    station = models.CharField(max_length=50, blank=True, help_text="e.g. Grill, Salad, Dessert")
    priority = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-priority", "created_at"]

    def __str__(self):
        return f"Ticket for {self.order_item}"
