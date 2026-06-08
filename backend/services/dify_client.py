import json
from typing import Any

import requests

from core.config import Settings
from core.models import DifyWorkflowResult


class DifyError(Exception):
    pass


class DifyConfigError(DifyError):
    pass


class DifyWorkflowError(DifyError):
    pass


class DifyClient:
    def __init__(
        self,
        api_base: str,
        api_key: str,
        user: str,
        script_output_key: str = "script_json",
        timeout_seconds: int = 60,
    ) -> None:
        self.api_base = api_base.rstrip("/")
        self.api_key = api_key
        self.user = user
        self.script_output_key = script_output_key
        self.timeout_seconds = timeout_seconds

        if not self.api_key:
            raise DifyConfigError("DIFY_API_KEY is not configured.")

    @classmethod
    def from_settings(cls, settings: Settings) -> "DifyClient":
        return cls(
            api_base=settings.dify_api_base,
            api_key=settings.dify_api_key,
            user=settings.dify_user,
            script_output_key=settings.dify_script_output_key,
        )

    def run_workflow(self, inputs: dict[str, Any]) -> DifyWorkflowResult:
        payload = {
            "inputs": inputs,
            "response_mode": "blocking",
            "user": self.user,
        }

        try:
            response = requests.post(
                f"{self.api_base}/workflows/run",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise DifyWorkflowError(f"Dify workflow request failed: {exc}") from exc

        data = response.json()
        workflow_data = data.get("data")
        if not isinstance(workflow_data, dict):
            raise DifyWorkflowError("Dify response is missing data object.")

        outputs = workflow_data.get("outputs")
        if not isinstance(outputs, dict):
            raise DifyWorkflowError("Dify response is missing data.outputs object.")

        script = self._extract_script(outputs)

        return DifyWorkflowResult(
            task_id=data.get("task_id"),
            workflow_run_id=data.get("workflow_run_id"),
            status=workflow_data.get("status"),
            outputs=outputs,
            script=script,
        )

    def _extract_script(self, outputs: dict[str, Any]) -> Any:
        if self.script_output_key in outputs:
            return self._parse_possible_json(outputs[self.script_output_key])

        if len(outputs) == 1:
            only_value = next(iter(outputs.values()))
            return self._parse_possible_json(only_value)

        available_keys = ", ".join(outputs.keys())
        raise DifyWorkflowError(
            f"Dify output key '{self.script_output_key}' was not found. "
            f"Available output keys: {available_keys}"
        )

    @staticmethod
    def _parse_possible_json(value: Any) -> Any:
        if not isinstance(value, str):
            return value

        text = value.strip()
        if not text:
            return value
        if text.startswith("```"):
            lines = text.splitlines()
            if len(lines) >= 3 and lines[-1].strip() == "```":
                text = "\n".join(lines[1:-1]).strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return value


def run_workflow(
    api_base: str,
    api_key: str,
    user: str,
    inputs: dict[str, Any],
    script_output_key: str = "script_json",
) -> Any:
    client = DifyClient(
        api_base=api_base,
        api_key=api_key,
        user=user,
        script_output_key=script_output_key,
    )
    return client.run_workflow(inputs).script
