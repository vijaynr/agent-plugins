import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
from unittest import TestCase, main
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "blackduck_vulnerabilities.py"
spec = importlib.util.spec_from_file_location("blackduck_vulnerabilities", SCRIPT)
bdcli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bdcli)

BASE = "https://blackduck.example"


def meta(href, links=None):
    return {"_meta": {"href": href, "links": links or []}}


PROJECT = {
    "name": "MyApp",
    "description": "demo",
    **meta(f"{BASE}/api/projects/p1", [{"rel": "versions", "href": f"{BASE}/api/projects/p1/versions"}]),
}
VERSION = {
    "versionName": "1.0",
    "phase": "DEVELOPMENT",
    **meta(
        f"{BASE}/api/projects/p1/versions/v1",
        [
            {"rel": "components", "href": f"{BASE}/api/projects/p1/versions/v1/components"},
            {"rel": "codelocations", "href": f"{BASE}/api/projects/p1/versions/v1/codelocations"},
        ],
    ),
}
COMPONENT_OPENSSL = {
    "componentName": "OpenSSL",
    "componentVersionName": "3.0.0",
    "component": f"{BASE}/api/components/c1",
    "componentVersion": f"{BASE}/api/components/c1/versions/cv1",
    "policyStatus": "IN_VIOLATION",
    "reviewStatus": "REVIEWED",
    "licenseRiskProfile": {"counts": [{"countType": "HIGH", "count": 1}]},
    "operationalRiskProfile": {"counts": [{"countType": "LOW", "count": 1}]},
    "securityRiskProfile": {"counts": [{"countType": "HIGH", "count": 1}]},
    "licenses": [{"licenseDisplay": "Apache-2.0"}],
    **meta(
        f"{BASE}/api/projects/p1/versions/v1/components/c1/versions/cv1",
        [{"rel": "matched-files", "href": f"{BASE}/api/projects/p1/versions/v1/components/c1/versions/cv1/matched-files"}],
    ),
}
COMPONENT_ZLIB = {
    "componentName": "zlib",
    "componentVersionName": "1.2.13",
    "component": f"{BASE}/api/components/c2",
    "componentVersion": f"{BASE}/api/components/c2/versions/cv2",
    "policyStatus": "NOT_IN_VIOLATION",
    "reviewStatus": "NOT_REVIEWED",
    "licenseRiskProfile": {"counts": [{"countType": "LOW", "count": 1}]},
    "operationalRiskProfile": {"counts": [{"countType": "MEDIUM", "count": 1}]},
    "securityRiskProfile": {"counts": [{"countType": "LOW", "count": 1}]},
    **meta(f"{BASE}/api/projects/p1/versions/v1/components/c2/versions/cv2"),
}
VULN_OPENSSL = {
    **COMPONENT_OPENSSL,
    "vulnerabilityWithRemediation": {
        "vulnerabilityName": "BDSA-2024-0001",
        "relatedVulnerability": f"{BASE}/api/vulnerabilities/CVE-2024-0001",
        "severity": "HIGH",
        "remediationStatus": "NEW",
    },
}
VULN_ZLIB = {
    **COMPONENT_ZLIB,
    "vulnerabilityWithRemediation": {
        "vulnerabilityName": "CVE-2023-9999",
        "severity": "LOW",
        "remediationStatus": "PATCHED",
    },
}


class FakeResponse:
    def __init__(self, status_code=200, data=None, text="", headers=None):
        self.status_code = status_code
        self._data = data if data is not None else {}
        self.text = text or json.dumps(self._data)
        self.headers = headers or {}

    def json(self):
        return self._data


class FakeSession:
    put_calls = []

    def __init__(self):
        self.verify = True
        self.get_calls = []

    def post(self, url, headers=None, **kwargs):
        assert url == f"{BASE}/api/tokens/authenticate"
        return FakeResponse(data={"bearerToken": "bearer", "expiresInMilliseconds": 7200000})

    def get(self, url, headers=None, params=None, timeout=None, allow_redirects=True):
        self.get_calls.append((url, params))
        if url == f"{BASE}/api/projects":
            return page([PROJECT])
        if url == f"{BASE}/api/projects/p1/versions":
            return page([VERSION])
        if url == f"{BASE}/api/projects/p1/versions/v1/components":
            items = [COMPONENT_OPENSSL, COMPONENT_ZLIB]
            q = (params or {}).get("q") or []
            if q and "OpenSSL" in q[0]:
                items = [COMPONENT_OPENSSL]
            return page(items)
        if url == f"{BASE}/api/projects/p1/versions/v1/vulnerable-bom-components":
            return page([VULN_OPENSSL, VULN_ZLIB])
        if url == f"{BASE}/api/vulnerabilities/BDSA-2024-0001":
            return FakeResponse(data={"name": "BDSA-2024-0001", "description": "important"})
        if url == f"{BASE}/api/projects/p1/versions/v1/codelocations":
            return page([{"name": "scan-1", "status": "COMPLETE", **meta(f"{BASE}/api/codelocations/l1")}])
        if url == f"{BASE}/api/projects/p1/versions/v1/components/c1/versions/cv1/matched-files":
            return page([{"uri": "file:///repo/libssl.so", "matchType": "FILE_DEPENDENCY"}])
        if url == f"{BASE}/api/licenses":
            return page([{"name": "Apache-2.0", **meta(f"{BASE}/api/licenses/l1")}])
        return FakeResponse(status_code=404, data={"error": url}, text="not found")

    def put(self, url, headers=None, json=None, timeout=None, allow_redirects=True):
        self.__class__.put_calls.append((url, headers, json))
        return FakeResponse(status_code=200, data={"ok": True})


def page(items):
    return FakeResponse(data={"totalCount": len(items), "items": items})


class BlackDuckCliReadOnlyTests(TestCase):
    def run_cli(self, argv):
        env = {"BLACKDUCK_URL": BASE, "BLACKDUCK_TOKEN": "token", "BLACKDUCK_VERIFY_SSL": "true"}
        FakeSession.put_calls = []
        with patch.dict(os.environ, env, clear=False), patch.object(bdcli.requests, "Session", FakeSession):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                bdcli.main(argv)
            return json.loads(out.getvalue())

    def test_list_projects(self):
        data = self.run_cli(["list-projects", "--query", "MyApp", "--exact"])
        self.assertEqual(data["totalProjects"], 1)
        self.assertEqual(data["projects"][0]["name"], "MyApp")

    def test_list_versions(self):
        data = self.run_cli(["list-versions", "--project", "MyApp", "--query", "1.0", "--exact"])
        self.assertEqual(data["totalVersions"], 1)
        self.assertEqual(data["versions"][0]["versionName"], "1.0")

    def test_list_components_with_filters(self):
        data = self.run_cli([
            "list-components", "--project", "MyApp", "--version", "1.0",
            "--query", "OpenSSL", "--exact", "--policy-status", "IN_VIOLATION",
            "--filter", "componentRisk:HIGH",
        ])
        self.assertEqual(data["totalComponents"], 1)
        self.assertEqual(data["components"][0]["componentName"], "OpenSSL")
        self.assertEqual(data["filters"]["filter"], ["componentRisk:HIGH"])

    def test_list_licenses(self):
        data = self.run_cli(["list-licenses", "--query", "Apache-2.0", "--exact"])
        self.assertEqual(data["totalLicenses"], 1)
        self.assertEqual(data["licenses"][0]["name"], "Apache-2.0")
        self.assertEqual(data["licenses"][0]["_meta"]["href"], f"{BASE}/api/licenses/l1")

    def test_list_components_with_friendly_risk_filters(self):
        data = self.run_cli([
            "list-components", "--project", "MyApp", "--version", "1.0",
            "--name", "OpenSSL", "--exact", "--review-status", "REVIEWED",
            "--license-risk", "HIGH", "--operational-risk", "LOW", "--security-risk", "HIGH",
            "--all",
        ])
        self.assertEqual(data["totalComponents"], 1)
        self.assertEqual(data["components"][0]["componentName"], "OpenSSL")
        self.assertEqual(data["components"][0]["reviewStatus"], "REVIEWED")
        self.assertEqual(data["filters"]["name"], "OpenSSL")
        self.assertIsNone(data["filters"]["limit"])

    def test_list_vulnerabilities_with_filters(self):
        data = self.run_cli([
            "list-vulnerabilities", "--project", "MyApp", "--version", "1.0",
            "--severity", "HIGH", "--status", "NEW", "--limit", "5",
        ])
        self.assertEqual(data["totalVulnerabilities"], 1)
        self.assertEqual(data["vulnerabilities"][0]["vulnerabilityName"], "BDSA-2024-0001")
        self.assertEqual(data["vulnerabilities"][0]["affectedComponent"]["componentName"], "OpenSSL")

    def test_misspelled_list_vulnerablities_alias(self):
        data = self.run_cli(["list-vulnerablities", "--project", "MyApp", "--version", "1.0", "--severity", "LOW"])
        self.assertEqual(data["totalVulnerabilities"], 1)
        self.assertEqual(data["vulnerabilities"][0]["vulnerabilityName"], "CVE-2023-9999")

    def test_get_vulnerability_details(self):
        data = self.run_cli([
            "get-vulnerability-details", "--project", "MyApp", "--version", "1.0",
            "--vuln-id", "BDSA-2024-0001", "--related-id", "CVE-2024-0001",
        ])
        self.assertEqual(data["details"]["name"], "BDSA-2024-0001")
        self.assertEqual(len(data["affectedComponents"]), 1)
        self.assertEqual(data["affectedComponents"][0]["component"]["componentName"], "OpenSSL")

    def test_get_code_location(self):
        data = self.run_cli([
            "get-code-location", "--project", "MyApp", "--version", "1.0",
            "--component", "OpenSSL", "--exact",
        ])
        self.assertEqual(data["totalMatches"], 1)
        self.assertEqual(data["versionCodeLocations"][0]["name"], "scan-1")
        self.assertEqual(data["matches"][0]["matchedFiles"][0]["path"], "file:///repo/libssl.so")

    def test_get_matched_files(self):
        data = self.run_cli([
            "get-matched-files", "--project", "MyApp", "--version", "1.0",
            "--component", "OpenSSL", "--exact", "--matched-file-limit", "10",
        ])
        self.assertEqual(data["totalComponents"], 1)
        self.assertEqual(data["matches"][0]["totalMatchedFiles"], 1)
        self.assertEqual(data["matches"][0]["matchedFiles"][0]["path"], "file:///repo/libssl.so")

    def test_update_component_review_license_and_usage(self):
        data = self.run_cli([
            "update-component", "--project", "MyApp", "--version", "1.0",
            "--component", "OpenSSL", "--exact",
            "--review-status", "REVIEWED",
            "--license", "Apache-2.0",
            "--usage", "DYNAMICALLY_LINKED",
            "--comment", "Reviewed by automation",
        ])
        self.assertTrue(data["ok"])
        self.assertEqual(data["componentsUpdated"], 1)
        self.assertEqual(data["requestedReviewStatus"], "REVIEWED")
        self.assertEqual(data["requestedLicense"]["href"], f"{BASE}/api/licenses/l1")
        self.assertEqual(data["requestedUsages"], ["DYNAMICALLY_LINKED"])
        self.assertEqual(FakeSession.put_calls[0][0], f"{BASE}/api/projects/p1/versions/v1/components/c1/versions/cv1")
        self.assertEqual(FakeSession.put_calls[0][2]["reviewStatus"], "REVIEWED")
        self.assertEqual(FakeSession.put_calls[0][2]["licenses"], [{"license": f"{BASE}/api/licenses/l1"}])
        self.assertEqual(FakeSession.put_calls[0][2]["usages"], ["DYNAMICALLY_LINKED"])
        self.assertEqual(FakeSession.put_calls[0][2]["comment"], "Reviewed by automation")


if __name__ == "__main__":
    main()
