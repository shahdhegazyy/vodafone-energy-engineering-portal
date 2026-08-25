from django.shortcuts import render
from cables.models import CableSelection
from rack_design.models import RackDesign


def home(request):
    return render(request, "portal/home.html")


def history(request):
    return render(request, "portal/history.html", {
        "cable_selections": CableSelection.objects.all(),
        "rack_designs": RackDesign.objects.all(),
    })
