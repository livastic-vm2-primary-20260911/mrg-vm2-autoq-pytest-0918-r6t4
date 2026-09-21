import copy
import datetime
import json
import os
from pathlib import Path
import urllib.error
import urllib.request
import uuid

OWNER = "vm2-billing-checkout-v7m3-260916"
REPO = "mrg-vm2-review-promotion-ci-0918-u9k3"
HEAD_SHA = "d69fdbac23d1cea146d009d861abcbb0cad49863"
PIPELINE = "VM2 Source Chain Victim Live 0921"
JOB = "vm2-sourcechain-victim-live-trigger-0921"
WEBHOOK = f"https://api.mergify.com/v1/ci/{OWNER}/repositories/{REPO}/buildkite/webhooks"


def _json_request(url, *, token, payload=None, bearer=False):
    headers = {"Accept": "application/json"}
    if payload is not None:
        headers["Content-Type"] = "application/json"
        headers["X-Buildkite-Token"] = token
        data = json.dumps(payload, separators=(",", ":")).encode()
        method = "POST"
    else:
        headers["Authorization"] = f"Bearer {token}"
        data = None
        method = "GET"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=15) as resp:
        raw = resp.read()
        return resp.status, json.loads(raw) if raw else None


def _pipeline(pair):
    slug = f"vm2-sourcechain-lateral-{pair}"
    root = f"https://buildkite.com/vm2/{slug}"
    api = f"https://api.buildkite.com/v2/organizations/vm2/pipelines/{slug}"
    return {
        "id": str(uuid.uuid4()),
        "graphql_id": f"pipeline-sourcechain-{pair}",
        "url": api,
        "web_url": root,
        "name": PIPELINE,
        "description": None,
        "slug": slug,
        "repository": f"git@github.com:{OWNER}/{REPO}.git",
        "branch_configuration": None,
        "default_branch": "main",
        "provider": {
            "id": "github",
            "webhook_url": "",
            "settings": {
                "publish_commit_status": True,
                "build_pull_requests": True,
                "build_pull_request_forks": False,
                "repository": f"{OWNER}/{REPO}",
                "trigger_mode": "code",
            },
        },
        "skip_queued_branch_builds": False,
        "cancel_running_branch_builds": False,
    }


def _job(pair, state, build_url, web_root, when, job_id, retry_id=None):
    failed = state == "failed"
    return {
        "id": job_id,
        "graphql_id": f"job-sourcechain-{job_id}",
        "type": "script",
        "name": JOB,
        "step_key": JOB,
        "step": {"id": "vm2-sourcechain-step", "signature": None},
        "priority": {"number": 0},
        "agent_query_rules": [],
        "state": state,
        "build_url": build_url,
        "web_url": f"{web_root}#{job_id}",
        "log_url": f"{build_url}/jobs/{job_id}/log",
        "raw_log_url": f"{build_url}/jobs/{job_id}/log.txt",
        "artifacts_url": "",
        "command": "true",
        "soft_failed": False,
        "exit_status": 1 if failed else 0,
        "signal": None,
        "signal_reason": None,
        "broken_reason": None,
        "artifact_paths": None,
        "created_at": when,
        "scheduled_at": when,
        "runnable_at": when,
        "concurrency_wait_time_ms": 0,
        "started_at": when,
        "finished_at": when,
        "expired_at": None,
        "retried": failed,
        "retried_in_job_id": retry_id if failed else None,
        "retries_count": 1,
        "retry_source": None,
        "retry_type": None if failed else "manual",
        "parallel_group_index": None,
        "parallel_group_total": None,
        "matrix": None,
        "agent": None,
        "retried_by": None,
    }


def _pair(pair):
    pipeline = _pipeline(pair)
    build_id = str(uuid.uuid4())
    fail_id = str(uuid.uuid4())
    retry_id = str(uuid.uuid4())
    number = 980 + pair
    base = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=pair * 10)
    fail_when = base.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    retry_when = (base + datetime.timedelta(seconds=5)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    build_url = f"{pipeline['url']}/builds/{number}"
    web_root = f"{pipeline['web_url']}/builds/{number}"
    fail_job = _job(pair, "failed", build_url, web_root, fail_when, fail_id, retry_id)
    retry_job = _job(pair, "passed", build_url, web_root, retry_when, retry_id)
    retry_job["retry_source"] = copy.deepcopy(fail_job)
    def event(job, state, when):
        build = {
            "id": build_id,
            "graphql_id": f"build-sourcechain-{pair}",
            "url": build_url,
            "web_url": web_root,
            "number": number,
            "state": state,
            "blocked": False,
            "message": "VM2 source-repo controlled cross-provider classifier",
            "commit": HEAD_SHA,
            "branch": "main",
            "env": {},
            "source": "api",
            "creator": {"id": str(uuid.uuid4()), "name": "VM2 Source Test", "email": "vm2-source@example.invalid"},
            "created_at": when,
            "scheduled_at": when,
            "started_at": when,
            "finished_at": when,
            "pipeline": copy.deepcopy(pipeline),
            "jobs": [],
        }
        return {"event": "job.finished", "job": job, "build": build, "pipeline": copy.deepcopy(pipeline), "sender": {"id": str(uuid.uuid4()), "name": "VM2 Source Test"}}
    return event(fail_job, "failed", fail_when), event(retry_job, "passed", retry_when)


def test_source_repo_code_can_poison_sibling_auto_retry_health():
    sentinel = Path("/tmp/vm2_sourcechain_lateral_0921.sent")
    if sentinel.exists():
        print("VM2_SOURCECHAIN_SKIP_ALREADY_SENT=1")
        return
    token = os.environ["MERGIFY_TOKEN"]
    try:
        status, app = _json_request("https://api.mergify.com/v1/application", token=token, bearer=True)
        print(f"VM2_SOURCECHAIN_APPLICATION status={status} scope={app.get('scope')} account={app.get('account_scope', {}).get('login')}")
    except urllib.error.HTTPError as exc:
        print(f"VM2_SOURCECHAIN_APPLICATION status={exc.code}")

    statuses = []
    for pair in range(1, 4):
        failed, retried = _pair(pair)
        for label, payload in (("fail", failed), ("retry", retried)):
            try:
                code, _ = _json_request(WEBHOOK, token=token, payload=payload)
            except urllib.error.HTTPError as exc:
                code = exc.code
            statuses.append(code)
            print(f"VM2_SOURCECHAIN_WEBHOOK pair={pair} phase={label} status={code}")
    assert statuses == [200, 200, 200, 200, 200, 200]
    sentinel.write_text("sent\n")
