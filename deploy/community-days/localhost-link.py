#################################################################################
#  Copyright (c) 2026 Contributors to the Eclipse Foundation
#
#  See the NOTICE file(s) distributed with this work for additional
#  information regarding copyright ownership.
#
#  This program and the accompanying materials are made available under the
#  terms of the Apache License, Version 2.0 which is available at
#  https://www.apache.org/licenses/LICENSE-2.0.
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.
#
#  AI Disclosure: This file was entirely AI-generated.
#  The AI-generated portions are made available under CC0-1.0 and not subject
#  to the project's license. The human contributor has reviewed and verified
#  that the code is correct.
#
#  SPDX-License-Identifier: Apache-2.0 AND CC0-1.0
#  Assisted-By: Claude Code (claude-opus-5-5)
#################################################################################
"""Runs a Python module with a forwarder from localhost:<port> to <host>:<port> in the same process.

Keycloak issues its tokens for http://localhost:8080/auth, the address the browser uses. Inside a
container, localhost is the container itself; this forwarder makes the same address reach the
Keycloak container, so the browser and the containers agree on the issuer.

    python localhost-link.py 8080 iam -m uvicorn tools.csp_standin.app:app --port 8100
"""
from __future__ import annotations

import os
import runpy
import socket
import sys
import threading


def _pipe(src: socket.socket, dst: socket.socket) -> None:
    try:
        while data := src.recv(65536):
            dst.sendall(data)
    except OSError:
        pass
    try:
        dst.shutdown(socket.SHUT_WR)
    except OSError:
        pass


def _link(client: socket.socket, host: str, port: int) -> None:
    with client:
        try:
            upstream = socket.create_connection((host, port), timeout=10)
        except OSError:
            return   # the client sees a closed connection, as with a stopped Keycloak
        with upstream:
            upstream.settimeout(None)
            back = threading.Thread(target=_pipe, args=(upstream, client), daemon=True)
            back.start()
            _pipe(client, upstream)
            back.join()


def _serve(server: socket.socket, host: str, port: int) -> None:
    while True:
        client, _ = server.accept()
        threading.Thread(target=_link, args=(client, host, port), daemon=True).start()


def main() -> None:
    port, host, flag, module, *args = sys.argv[1:]
    if flag != "-m":
        raise SystemExit(__doc__)
    for address, family in (("127.0.0.1", socket.AF_INET), ("::1", socket.AF_INET6)):
        try:
            server = socket.create_server((address, int(port)), family=family)
        except OSError:
            continue   # no IPv6 in this container
        threading.Thread(target=_serve, args=(server, host, int(port)), daemon=True).start()
    sys.argv = [module, *args]
    sys.path.insert(0, os.getcwd())   # as `python -m` does
    runpy.run_module(module, run_name="__main__", alter_sys=True)


if __name__ == "__main__":
    main()
