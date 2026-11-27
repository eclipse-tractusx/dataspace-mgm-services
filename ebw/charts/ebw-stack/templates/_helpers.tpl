{{/*
Copyright (c) 2026 Contributors to the Eclipse Foundation

See the NOTICE file(s) distributed with this work for additional
information regarding copyright ownership.

This program and the accompanying materials are made available under the
terms of the Apache License, Version 2.0 which is available at
https://www.apache.org/licenses/LICENSE-2.0.

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
License for the specific language governing permissions and limitations
under the License.

AI Disclosure: This file was entirely AI-generated.
The AI-generated portions are made available under CC0-1.0 and not subject
to the project's license. The human contributor has reviewed and verified
that the code is correct.

SPDX-License-Identifier: Apache-2.0 AND CC0-1.0
Assisted-By: Claude Code (claude-fable-5-2)
*/}}

{{/*
Expand the name of the chart.
*/}}
{{- define "ebw-stack.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name (max 63 characters, DNS naming spec).
*/}}
{{- define "ebw-stack.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Chart name and version as used by the chart label.
*/}}
{{- define "ebw-stack.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "ebw-stack.labels" -}}
helm.sh/chart: {{ include "ebw-stack.chart" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- with .Values.commonLabels }}
{{ toYaml . }}
{{- end }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "ebw-stack.selectorLabels" -}}
app.kubernetes.io/name: {{ include "ebw-stack.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Image of the three containers.
*/}}
{{- define "ebw-stack.image" -}}
{{- printf "%s:%s" .Values.image.repository (default .Chart.AppVersion .Values.image.tag) }}
{{- end }}

{{/*
Public addresses of the three services: scheme of `publicScheme` and the host name of the service.
*/}}
{{- define "ebw-stack.connectorUrl" -}}
{{- printf "%s://%s" .Values.publicScheme (required "connector.host is required" .Values.connector.host) }}
{{- end }}

{{- define "ebw-stack.businessWalletUrl" -}}
{{- printf "%s://%s" .Values.publicScheme (required "businessWallet.host is required" .Values.businessWallet.host) }}
{{- end }}

{{- define "ebw-stack.testToolsUrl" -}}
{{- printf "%s://%s" .Values.publicScheme (required "testTools.host is required" .Values.testTools.host) }}
{{- end }}

{{/*
Name of the claim with keys and data.
*/}}
{{- define "ebw-stack.claimName" -}}
{{- default (include "ebw-stack.fullname" .) .Values.persistence.existingClaim }}
{{- end }}

{{/*
Environment variables that all three containers get: the public addresses of the stack and the values of `env`.
*/}}
{{- define "ebw-stack.commonEnv" -}}
- name: CONNECTOR_URL
  value: {{ include "ebw-stack.connectorUrl" . | quote }}
- name: BUSINESS_WALLET_URL
  value: {{ include "ebw-stack.businessWalletUrl" . | quote }}
- name: TEST_TOOLS_URL
  value: {{ include "ebw-stack.testToolsUrl" . | quote }}
- name: RESPONSE_MODE
  value: {{ .Values.responseMode | quote }}
{{- range $name, $value := .Values.env }}
- name: {{ $name }}
  value: {{ $value | toString | quote }}
{{- end }}
{{- with .Values.extraEnv }}
{{ toYaml . }}
{{- end }}
{{- end }}

{{/*
Volume mounts that all three containers get.
*/}}
{{- define "ebw-stack.commonMounts" -}}
- name: data
  mountPath: /data
- name: tmp
  mountPath: /tmp
{{- with .Values.extraVolumeMounts }}
{{ toYaml . }}
{{- end }}
{{- end }}

{{/*
Liveness and readiness probe of one container. Call with (dict "path" "/jwks" "port" "connector").
*/}}
{{- define "ebw-stack.probes" -}}
livenessProbe:
  httpGet:
    path: {{ .path }}
    port: {{ .port }}
  initialDelaySeconds: 10
  periodSeconds: 20
  timeoutSeconds: 5
  failureThreshold: 3
readinessProbe:
  httpGet:
    path: {{ .path }}
    port: {{ .port }}
  initialDelaySeconds: 3
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3
{{- end }}
