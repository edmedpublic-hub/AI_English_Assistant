# views/comprehension/hub.py
from rest_framework.response import Response
from rest_framework.views import APIView

class ComprehensionHubView(APIView):
    """
    Central hub for comprehension activities.
    Returns available focuses and entry points.
    """

    def get(self, request, chunk_id):
        return Response({
            "message": "Comprehension hub",
            "chunk_id": chunk_id,
            "routes": {
                "teach": f"/api/comprehension/{chunk_id}/teach/",
                "practice": f"/api/comprehension/{chunk_id}/practice/",
                "test": f"/api/comprehension/{chunk_id}/test/",
            }
        })