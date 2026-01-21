from django.shortcuts import render, get_object_or_404
from ..models import Unit
from ..serializers import UnitSerializer

def unit_list(request):
    units = Unit.objects.all()
    serializer = UnitSerializer(units, many=True)
    return render(
        request,
        "content/main/unit_list.html",
        {
            "units": units,
            "units_data": serializer.data,
        }
    )

def unit_detail(request, pk):
    unit = get_object_or_404(Unit, pk=pk)
    serializer = UnitSerializer(unit)
    return render(
        request,
        "content/main/unit_detail.html",
        {
            "unit": unit,
            "unit_data": serializer.data,
        }
    )
