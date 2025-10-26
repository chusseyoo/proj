import os
import tempfile

from reporting.infrastructure.storage.adapter import FilesystemStorageAdapter


def test_filesystem_storage_adapter_writes_and_returns_path(tmp_path):
    adapter = FilesystemStorageAdapter(base_dir=str(tmp_path))

    content = b"hello,world"
    filename = "testfile.txt"

    final_path = adapter.save_export(content, filename)

    assert os.path.exists(final_path)

    with open(final_path, "rb") as fh:
        read = fh.read()

    assert read == content
