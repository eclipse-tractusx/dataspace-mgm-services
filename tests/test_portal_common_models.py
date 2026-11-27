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
"""The shared model bases of `portal_common.models` (FRAMEWORK 4.1, 4.4)."""
import pytest
from pydantic import ValidationError

from portal_common.models import ApiModel, Bpnl, Page, RequestBody, StepRequest, StepResult, Uuid

RUN = "00000000-0000-4000-8000-000000000002"
PROCESS = "00000000-0000-4000-8000-000000000001"


class Company(ApiModel):
    company_id: Uuid
    legal_name: str
    bpn: Bpnl | None = None


class Rename(RequestBody):
    legal_name: str
    short_name: str | None = None


def test_api_model_reads_both_names_and_writes_camel_case():
    by_alias = Company.model_validate({"companyId": RUN, "legalName": "ACME"})
    by_name = Company(company_id=RUN, legal_name="ACME")
    assert by_alias == by_name
    assert by_alias.to_json() == {"companyId": RUN, "legalName": "ACME"}


def test_identifier_formats_are_checked():
    with pytest.raises(ValidationError):
        Company(company_id="not-a-uuid", legal_name="ACME")
    with pytest.raises(ValidationError):
        Company(company_id=RUN, legal_name="ACME", bpn="BPNS000000000001")
    assert Company(company_id=RUN, legal_name="ACME", bpn="BPNL000000000001").bpn == "BPNL000000000001"


def test_request_body_refuses_unknown_fields_and_explicit_null():
    assert Rename.model_validate({"legalName": "ACME"}).short_name is None
    with pytest.raises(ValidationError, match="shortName must not be null"):
        Rename.model_validate({"legalName": "ACME", "shortName": None})
    with pytest.raises(ValidationError):
        Rename.model_validate({"legalName": "ACME", "unknown": 1})


def test_step_request_ignores_the_rest_of_the_step_input():
    step = StepRequest.model_validate({"processId": PROCESS, "stepRunId": RUN, "companyId": PROCESS})
    assert (step.process_id, step.step_run_id) == (PROCESS, RUN)
    with pytest.raises(ValidationError):
        StepRequest.model_validate({"processId": PROCESS})


def test_step_result_envelope():
    step = StepRequest(process_id=PROCESS, step_run_id=RUN)
    assert StepResult.done(step, {"companyId": PROCESS}).to_json() == {
        "stepRunId": RUN, "state": "DONE", "result": {"companyId": PROCESS}}
    assert StepResult.running(None, {}).to_json() == {"state": "RUNNING", "result": {}}


def test_page_of_slices_and_counts():
    page = Page.of(list(range(45)), page=2, size=20)
    assert page.to_json() == {"items": [40, 41, 42, 43, 44], "page": 2, "size": 20, "total": 45}
    assert Page.of([], None, None).to_json() == {"items": [], "page": 0, "size": 20, "total": 0}
    typed = Page[Company].of([Company(company_id=RUN, legal_name="ACME")])
    assert typed.to_json()["items"] == [{"companyId": RUN, "legalName": "ACME"}]
    with pytest.raises(ValidationError):
        Page.of([1], page=0, size=101)
