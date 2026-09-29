from django.shortcuts import render

def home(request):
    """Public marketing homepage."""
    return render(request, "landing/home.html")