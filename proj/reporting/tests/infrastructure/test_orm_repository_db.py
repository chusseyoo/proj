from django.test import TestCase

from reporting.infrastructure.repositories.orm_repository import OrmReportRepository
from reporting.models import Report


class OrmReportRepositoryTests(TestCase):
    def setUp(self):
        self.repo = OrmReportRepository()

    def test_create_and_get_report(self):
        metadata = {
            "session": {"id": 10},
            "students": [{"student_id": "s1", "status": "Present"}],
            "statistics": {"total_students": 1, "present_count": 1},
        }

        created = self.repo.create_report(10, 42, metadata)
        self.assertIsNotNone(created.pk)

        fetched = self.repo.get_report(created.pk)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.pk, created.pk)

    def test_get_report_details_and_missing(self):
        metadata = {"session": {"id": 11}, "students": [], "statistics": {}}
        created = self.repo.create_report(11, 3, metadata)

        details = self.repo.get_report_details(created.pk)
        self.assertIsInstance(details, dict)
        self.assertEqual(details.get("session", {}).get("id"), 11)

        # missing report id returns None
        self.assertIsNone(self.repo.get_report_details(9999))

    def test_update_export_details_and_idempotence(self):
        metadata = {"session": {"id": 20}, "students": [], "statistics": {}}
        created = self.repo.create_report(20, 5, metadata)

        # update export details
        self.repo.update_export_details(created.pk, "/tmp/out.csv", "csv")
        refreshed = Report.objects.get(pk=created.pk)
        self.assertEqual(refreshed.file_path, "/tmp/out.csv")
        self.assertEqual(refreshed.file_type, "csv")

        # second update should raise because it's already exported
        with self.assertRaises(ValueError):
            self.repo.update_export_details(created.pk, "/tmp/again.csv", "csv")
