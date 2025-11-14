"""Tests that verify handler scaffolds raise NotImplementedError.

These handlers are currently thin scaffolds; tests assert the current
contract (they raise NotImplementedError) so future implementations
will need to change tests accordingly.
"""
from reporting.interfaces.api.handlers.generate_report_handler import GenerateReportHandler
from reporting.interfaces.api.handlers.export_report_handler import ExportReportHandler
from reporting.interfaces.api.handlers.download_report_handler import DownloadReportHandler


def test_generate_report_handler_not_implemented():
    handler = GenerateReportHandler(generate_report_use_case=None)
    try:
        handler.handle(None, 1)
    except NotImplementedError:
        raised = True
    else:
        raised = False
    assert raised


def test_export_and_download_handlers_not_implemented():
    exp = ExportReportHandler(export_use_case=None)
    dl = DownloadReportHandler(storage_adapter=None, report_repository=None)

    for h in (exp, dl):
        try:
            # call with minimal args expecting NotImplementedError
            if isinstance(h, ExportReportHandler):
                h.handle(None, 1, {})
            else:
                h.handle(None, 1)
        except NotImplementedError:
            ok = True
        else:
            ok = False
        assert ok
