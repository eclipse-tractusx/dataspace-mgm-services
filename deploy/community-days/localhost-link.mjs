/********************************************************************************
 * Copyright (c) 2026 Contributors to the Eclipse Foundation
 *
 * See the NOTICE file(s) distributed with this work for additional
 * information regarding copyright ownership.
 *
 * This program and the accompanying materials are made available under the
 * terms of the Apache License, Version 2.0 which is available at
 * https://www.apache.org/licenses/LICENSE-2.0.
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations
 * under the License.
 *
 * AI Disclosure: This file was entirely AI-generated.
 * The AI-generated portions are made available under CC0-1.0 and not subject
 * to the project's license. The human contributor has reviewed and verified
 * that the code is correct.
 *
 * SPDX-License-Identifier: Apache-2.0 AND CC0-1.0
 * Assisted-By: Claude Code (claude-opus-5-5)
 ********************************************************************************/

// Starts the portal BFF with a forwarder from localhost:8080 to the Keycloak container in the same process.
// Keycloak issues its tokens for http://localhost:8080/auth, the address the browser uses; the BFF reads the
// discovery document from that issuer and checks it, so inside the container localhost:8080 must reach Keycloak.
// LINK_PORT and LINK_HOST name the forwarded port and the target host; LINK_MAIN the module to start.
import net from 'node:net';

const port = Number(process.env.LINK_PORT ?? '8080');
const host = process.env.LINK_HOST ?? 'iam';

function listen(address) {
  const server = net.createServer((client) => {
    const upstream = net.connect(port, host);
    client.pipe(upstream).pipe(client);
    client.on('error', () => upstream.destroy());
    upstream.on('error', () => client.destroy());
  });
  return new Promise((resolve) => {
    server.once('error', () => resolve(false)); // no IPv6 in this container
    server.listen(port, address, () => resolve(true));
  });
}

await listen('127.0.0.1');
await listen('::1');
await import(process.env.LINK_MAIN ?? '/app/src/main.ts');
