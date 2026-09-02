import importlib.util
import json
import unittest
from pathlib import Path


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
            }.issubset(codes)
        )


if __name__ == "__main__":
    unittest.main()
