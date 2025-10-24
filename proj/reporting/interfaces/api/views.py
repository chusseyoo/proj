"""DRF view wrappers for reporting endpoints (scaffold).

These views should be registered in `urls.py` and call the handlers/use-cases
prepared in the application layer.
"""
try:
    from rest_framework.views import APIView
    from rest_framework.response import Response
    from rest_framework import status
except Exception:  # pragma: no cover
    APIView = object
    Response = dict
    status = type("S", (), {"HTTP_201_CREATED": 201})


class GenerateReportView(APIView):
    def post(self, request, session_id: int):
        # TODO: instantiate or inject GenerateReportHandler and call it
        return Response({"detail": "Not implemented"}, status=status.HTTP_201_CREATED)
