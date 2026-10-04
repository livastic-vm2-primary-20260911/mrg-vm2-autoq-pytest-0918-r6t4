import json
import os
import subprocess

SOURCE_ACCOUNT = "vm2-billing-checkout-v7m3-260916"
DEST_ACCOUNT = "livastic-vm2-lab-20260911-g3a9"
SIBLING = "mrg-vm2-source-secret-sibling-0923-c8p4"
SIBLING_PR = 2
SCOPE = "vm2-transfer-ci-key-cross-tenant-1004"


def _curl(url, token, method="GET", payload=None):
    cmd = [
        "curl", "-sS",
        "-H", f"Authorization: Bearer {token}",
        "-H", "Accept: application/json",
        "-H", "User-Agent: vm2-transfer-ci-key-1004",
        "-X", method,
    ]
    if payload is not None:
        cmd += ["-H", "Content-Type: application/json", "--data", json.dumps(payload, separators=(",", ":"))]
    cmd += ["-w", "\n%{http_code}", url]
    cp = subprocess.run(cmd, check=False, capture_output=True, text=True)
    lines = cp.stdout.splitlines()
    status = int(lines[-1]) if lines and lines[-1].isdigit() else 0
    body = "\n".join(lines[:-1])
    return status, body


def test_transfer_inherited_ci_key_identity_and_former_tenant_scope():
    token = os.environ["MERGIFY_TOKEN"]
    current_repo = os.environ.get("GITHUB_REPOSITORY", "")
    current_owner = current_repo.split("/", 1)[0] if "/" in current_repo else ""

    app_status, app_body = _curl("https://api.mergify.com/v1/application", token)
    app = json.loads(app_body) if app_body else {}
    account = app.get("account_scope") or {}

    print(f"VM2_TRANSFER_CURRENT_REPO={current_repo}")
    print(f"VM2_TRANSFER_APPLICATION_HTTP={app_status}")
    print(f"VM2_TRANSFER_APPLICATION_SCOPE={app.get('scope')}")
    print(f"VM2_TRANSFER_APPLICATION_ACCOUNT={account.get('login')}")

    assert app_status == 200
    assert app.get("scope") == "ci"
    assert account.get("login") == SOURCE_ACCOUNT

    if current_owner != DEST_ACCOUNT:
        print("VM2_TRANSFER_STAGE=SOURCE_IDENTITY_ONLY")
        return

    print("VM2_TRANSFER_STAGE=DESTINATION_FORMER_TENANT_SCOPE_WRITE")
    scopes_url = f"https://api.mergify.com/v1/repos/{SOURCE_ACCOUNT}/{SIBLING}/pulls/{SIBLING_PR}/scopes"
    put_status, put_body = _curl(
        scopes_url,
        token,
        method="PUT",
        payload={"scopes": [SCOPE], "all_scopes": False},
    )
    print(f"VM2_TRANSFER_SIBLING_SCOPE_PUT_HTTP={put_status}")
    if put_body:
        print(f"VM2_TRANSFER_SIBLING_SCOPE_PUT_BODY={put_body[:200]}")
    assert put_status == 204

    get_status, get_body = _curl(scopes_url, token)
    print(f"VM2_TRANSFER_SIBLING_SCOPE_GET_HTTP={get_status}")
    scopes = json.loads(get_body) if get_body else {}
    print(f"VM2_TRANSFER_SIBLING_SCOPE_READBACK={json.dumps(scopes, sort_keys=True)[:500]}")
    assert get_status == 200
    assert SCOPE in json.dumps(scopes)
