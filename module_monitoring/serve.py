"""The one server of module_monitoring: the page and the two stores it reads, three prefixes and nothing else.

    GET /                        the page, index.html
    GET /<file>                  a file of the page — a direct child of module_monitoring/ ending .html, .js or .css
    GET /status/<path>           a file of the status store: the four snapshots
    GET /run_records/<path>      a file of the run-records store: index.json and the records it lists

Every other path is 404, and so is a directory: nothing is listed. A path is translated the way http.server translates
it, from the directory its prefix names.
"""

from __future__ import annotations

import os
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from . import config


class DashboardHandler(SimpleHTTPRequestHandler):
    """The page's files and the two stores' files, each served as http.server serves a file."""

    def translate_path(self, path: str) -> str | None:
        """The file a request names, or None when no prefix claims it: a store's prefix translates the rest of the path
        from that store, and any other path is a page file only when it is one direct child with a page suffix."""
        for prefix, store in config.STORE_DIR_BY_ROUTE_PREFIX.items():
            if path.startswith(prefix):
                self.directory = str(store)
                return super().translate_path(path.removeprefix(prefix[:-1]))
        self.directory = str(config.MODULE_MONITORING_DIR)
        translated = super().translate_path(path).rstrip("/")
        if translated == self.directory:
            return os.path.join(self.directory, config.PAGE_INDEX_FILE_NAME)
        if os.path.dirname(translated) == self.directory and translated.endswith(config.PAGE_FILE_SUFFIXES):
            return translated
        return None

    def send_head(self):
        """A claimed path that is a file, served as http.server serves it; anything else 404."""
        path = self.translate_path(self.path)
        if path is None or not os.path.isfile(path):
            self.send_error(HTTPStatus.NOT_FOUND)
            return None
        return super().send_head()


def main() -> int:
    server = ThreadingHTTPServer((config.BIND_ADDRESS, config.CONTAINER_PORT), DashboardHandler)
    print(f"dashboard at http://{config.BIND_ADDRESS}:{config.CONTAINER_PORT}/", flush=True)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
