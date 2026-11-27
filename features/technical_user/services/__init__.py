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
#  The software is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
#  CONDITIONS OF ANY KIND, either express or implied. See the License for the
#  specific language governing permissions and limitations under the License.
#
#  AI Disclosure: This file was entirely AI-generated.
#  The AI-generated portions are made available under CC0-1.0 and not subject
#  to the project's license. The human contributor has reviewed and verified
#  that the code is correct.
#
#  SPDX-License-Identifier: Apache-2.0 AND CC0-1.0
#  Assisted-By: GitHub Copilot (GPT-5.1)
#################################################################################
"""C2-M3 application services: `queries` read, `commands` are people's operations, `steps` are Process Orchestration's.

The modules return the pydantic models of `models/responses.py`. This package offers the same functions with the
JSON answer (`to_wire`) for `interface.py`, so an in-process caller gets what an HTTP caller gets; the controllers
call the interface and declare the models as `response_model`."""
from __future__ import annotations

import functools
from collections.abc import Callable
from typing import Any

from ..managers import iam as _iam
from ..managers.technical_user_repository import repository as _repository
from ..models.responses import to_wire
from . import commands, queries, roles, steps
from .process_stub import handle_event


def _wire(function: Callable) -> Callable:
    @functools.wraps(function)
    def answer(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401 (the answer of the wrapped function as JSON)
        return to_wire(function(*args, **kwargs))
    return answer


create_technical_user = _wire(commands.create_technical_user)
update_technical_user = _wire(commands.update_technical_user)
delete_technical_user = _wire(commands.delete_technical_user)
rotate_credentials = _wire(commands.rotate_credentials)
rotate_subscription_credentials = _wire(commands.rotate_subscription_credentials)
get_technical_user = _wire(queries.get_technical_user)
get_any_technical_user = _wire(queries.get_any_technical_user)
list_technical_users = _wire(queries.list_technical_users)
list_all_technical_users = _wire(queries.list_all_technical_users)
check_technical_user = _wire(queries.check_technical_user)
list_assignable_roles = _wire(roles.list_assignable_roles)
list_technical_roles = _wire(roles.list_technical_roles)
create_for_subscription = _wire(steps.create_for_subscription)
apply_wallet_access = _wire(steps.apply_wallet_access)
delete = _wire(steps.delete)
disable_company_technical_users = _wire(steps.disable_company_technical_users)
enable_company_technical_users = _wire(steps.enable_company_technical_users)
disable_subscription_technical_users = _wire(steps.disable_subscription_technical_users)


def reset() -> None:
    _repository.reset()
    _iam.reset()


__all__ = [
    "apply_wallet_access", "check_technical_user", "create_for_subscription", "create_technical_user", "delete",
    "delete_technical_user", "disable_company_technical_users", "disable_subscription_technical_users",
    "enable_company_technical_users", "get_any_technical_user", "get_technical_user", "handle_event",
    "list_all_technical_users", "list_assignable_roles", "list_technical_roles", "list_technical_users", "reset",
    "rotate_credentials", "rotate_subscription_credentials", "update_technical_user",
]
