"""DRF serializers for reporting API (scaffold).

These serializers are small placeholders. Implement field mappings and
nested serializers as required by the ReportDTO.
"""
try:
    from rest_framework import serializers
except Exception:  # pragma: no cover - DRF may not be available in tooling
    # Minimal fallback to avoid import errors when reading files
    class serializers:  # type: ignore
        class Serializer:  # type: ignore
            pass


class ExportReportRequestSerializer(serializers.Serializer):
    file_type = serializers.ChoiceField(choices=["csv", "excel"])


class ReportResponseSerializer(serializers.Serializer):
    # TODO: implement nested fields mapping to ReportDTO
    pass
