import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "rd_client",
    ROOT / "example-scripts" / "rd_client.py",
)
rd_client = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(rd_client)


class ErrorParserTests(unittest.TestCase):
    def test_parses_v2_and_all_v1_shapes(self):
        cases = [
            (
                {
                    "error": {
                        "code": "rate_limited",
                        "message": "Too many requests.",
                        "request_id": "request-v2",
                    }
                },
                "rate_limited",
                "Too many requests.",
            ),
            ({"detail": "Not Found"}, None, "Not Found"),
            (
                {"detail": [{"msg": "Invalid token."}]},
                None,
                "Invalid token.",
            ),
            (
                {
                    "detail": {
                        "code": "inference_failed",
                        "message": "Unable to run inference.",
                    }
                },
                "inference_failed",
                "Unable to run inference.",
            ),
        ]
        for body, code, message in cases:
            error = rd_client.parse_api_error(
                status_code=400,
                body=body,
                headers={},
            )
            self.assertEqual(error.code, code)
            self.assertEqual(error.message, message)

    def test_preserves_header_request_id_and_retry_after(self):
        error = rd_client.parse_api_error(
            status_code=503,
            body=None,
            headers={
                "X-Request-ID": "edge-request",
                "Retry-After": "17",
            },
        )
        self.assertEqual(error.request_id, "edge-request")
        self.assertEqual(error.retry_after, "17")
        self.assertNotIn("[object Object]", str(error))


class InferenceAdmissionTests(unittest.TestCase):
    @patch.object(rd_client.requests, "post")
    def test_paid_v2_submission_uses_caller_idempotency_key(self, post: Mock):
        post.return_value.ok = True
        post.return_value.json.return_value = {"status": "accepted", "task_id": "task-1"}

        rd_client._submit_inference(
            {"width": 64, "height": 64, "num_images": 1},
            "rdpk-test",
            "saved-key",
        )

        self.assertEqual(post.call_args.kwargs["headers"]["Idempotency-Key"], "saved-key")

    @patch.object(rd_client.requests, "post")
    def test_cost_check_does_not_send_idempotency_key(self, post: Mock):
        post.return_value.ok = True
        post.return_value.json.return_value = {"balance_cost": 0.01}

        rd_client._submit_inference(
            {"width": 64, "height": 64, "num_images": 1, "check_cost": True},
            "rdpk-test",
            "unused-key",
        )

        self.assertNotIn("Idempotency-Key", post.call_args.kwargs["headers"])


class ContractArtifactTests(unittest.TestCase):
    def test_v2_openapi_and_catalog_use_the_canonical_error_contract(self):
        openapi = json.loads((ROOT / "contracts" / "v2" / "openapi.json").read_text())
        catalog = json.loads(
            (ROOT / "contracts" / "v2" / "error-codes.json").read_text()
        )

        self.assertEqual(openapi["info"]["version"], "2.0.0")
        self.assertIn("V2ErrorResponse", openapi["components"]["schemas"])
        self.assertNotIn("/inferences/legacy", openapi["paths"])
        self.assertFalse(
            any(path.startswith("/external-credits") for path in openapi["paths"])
        )
        codes = {definition["code"] for definition in catalog["errors"]}
        self.assertTrue(
            {
                "invalid_token",
                "not_enough_balance",
                "inference_failed",
                "internal_error",
                "style_not_found",
            }.issubset(codes)
        )
        create_style = openapi["components"]["schemas"]["ExternalRDProStyleCreate"]
        self.assertIn("reference_images", create_style["required"])
        self.assertEqual(
            create_style["properties"]["reference_images"]["minItems"],
            1,
        )
        self.assertEqual(
            create_style["properties"]["reference_images"]["maxItems"],
            1,
        )
        inference = openapi["components"]["schemas"]["ExternalInferenceInputNeo"]
        self.assertEqual(inference["properties"]["prompt"]["default"], "")
        self.assertNotIn("prompt", inference["required"])
        selector = openapi["components"]["schemas"]["ExternalStyleSelectorItem"]
        self.assertIn("prompt_requirement", selector["properties"])
        self.assertIn("supports_frames_duration", selector["properties"])
        status = openapi["components"]["schemas"]["PublicStatusResponse"]
        self.assertEqual(status["properties"]["updated_at"]["type"], "integer")
        inference_headers = {
            parameter["name"]
            for parameter in openapi["paths"]["/inferences"]["post"]["parameters"]
        }
        self.assertIn("Idempotency-Key", inference_headers)
        self.assertTrue(
            {
                "invalid_idempotency_key",
                "idempotency_async_required",
                "idempotency_conflict",
                "idempotency_backend_unavailable",
            }.issubset(codes)
        )

    def test_llms_summary_matches_v2_auth_and_async_contracts(self):
        llms = (ROOT / "llms.txt").read_text()

        self.assertIn("Invalid token on this endpoint -> 401 invalid_token.", llms)
        self.assertNotIn("Invalid token on this endpoint -> 403.", llms)
        self.assertIn(
            "v2 generation is always async",
            llms,
        )
        self.assertIn("Poll GET /v2/inferences/tasks/{task_id}", llms)
        self.assertIn(
            "recover the accepted task with GET /v2/inferences/tasks",
            llms,
        )
        self.assertIn("persist a unique Idempotency-Key", llms)
        self.assertIn('"supports_frames_duration"', llms)
        self.assertIn("updated_at is Unix seconds", llms)
        self.assertIn('"reference_images": ["<base64>"] (exactly 1, required)', llms)


if __name__ == "__main__":
    unittest.main()
