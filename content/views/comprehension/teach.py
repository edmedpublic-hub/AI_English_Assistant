# views/comprehension/teach.py
from rest_framework import generics
from content.models.comprehension import ChunkComprehensionFocus
from content.serializers.comprehension import ChunkComprehensionFocusSerializer

class ComprehensionTeachView(generics.RetrieveAPIView):
    """
    Deliver comprehension teaching material for a focus.
    """
    queryset = ChunkComprehensionFocus.objects.all()
    serializer_class = ChunkComprehensionFocusSerializer
    lookup_field = "id"