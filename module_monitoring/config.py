"""Static configuration of module_monitoring: the server's address, the page's own files and the two stores it serves
beside them — the one place this module builds a path.

The page reads everything by a relative path: its own files beside it, the snapshots under status/ and the run records
under run_records/, each prefix one store — the store contract, one variable per store. The per-asset artifact paths
stay in the configs of the modules that produce them; this module reads no artifacts store.
"""

import os
from pathlib import Path

# ---- the dashboard's server
CONTAINER_PORT = 8900                    # the port the server listens on inside its container; PORT is only the host side of the mapping, measured by the Makefile
BIND_ADDRESS = "0.0.0.0"                 # every interface of the container's own namespace; compose publishes the dashboard on 127.0.0.1

# ---- what it serves: the page's files, a direct child of this module's directory with one of these suffixes, the page
# itself under /, and the two stores the page reads, each under the prefix the page names it by
MODULE_MONITORING_DIR = Path(__file__).resolve().parent
PAGE_FILE_SUFFIXES = (".html", ".js", ".css")
PAGE_INDEX_FILE_NAME = "index.html"
# twice by extraction
STORE_RUN_RECORDS_DIR = Path(os.environ["STORE_RUN_RECORDS_DIR"])
# twice by extraction
STORE_STATUS_DIR = Path(os.environ["STORE_STATUS_DIR"])
STORE_DIR_BY_ROUTE_PREFIX = {"/status/": STORE_STATUS_DIR, "/run_records/": STORE_RUN_RECORDS_DIR}
