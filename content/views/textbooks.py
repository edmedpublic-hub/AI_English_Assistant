from django.shortcuts import render, get_object_or_404
from ..models import Textbook
from ..serializers import TextbookSerializer

def textbook_list(request):
    textbooks = Textbook.objects.all()
    serializer = TextbookSerializer(textbooks, many=True)
    return render(
        request,
        "content/textbook_list.html",
        {
            "textbooks": textbooks,
            "textbooks_data": serializer.data,
        }
    )

def textbook_detail(request, pk):
    textbook = get_object_or_404(Textbook, pk=pk)
    serializer = TextbookSerializer(textbook)
    return render(
        request,
        "content/textbook_detail.html",
        {
            "textbook": textbook,
            "textbook_data": serializer.data,
        }
    )
