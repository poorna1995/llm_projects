import os
import json
import time
from typing import Optional
import httpx
from pathlib import Path

try:
    from azure.servicebus import ServiceBusClient  # type: ignore
except Exception:  # pragma: no cover
    ServiceBusClient = None  # type: ignore


def process_message(message_body: dict) -> None:
    job_id = message_body.get("job_id")
    resume_text = (message_body.get("resume_text") or "").strip()
    job_description = (message_body.get("job_description") or "").strip()

    bento_url = os.getenv("BENTO_URL", "http://bento:3000")

    results = {}
    try:
        with httpx.Client(timeout=10) as client:
            if resume_text:
                r = client.post(f"{bento_url}/parse_resume", json={"text": resume_text})
                r.raise_for_status()
                results["parsed"] = r.json()
                r = client.post(f"{bento_url}/extract_skills", json={"text": resume_text})
                r.raise_for_status()
                results["skills"] = r.json()
            if resume_text or job_description:
                r = client.post(
                    f"{bento_url}/score_match",
                    json={"resume_text": resume_text, "job_description": job_description},
                )
                r.raise_for_status()
                results["score"] = r.json()
    except Exception as e:
        results["error"] = str(e)

    out_dir = Path("/workspace/output") / f"run-{job_id}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "bento_results.json"
    out_file.write_text(json.dumps(results, indent=2))
    print(f"processed job {job_id} -> {out_file}")


def main() -> None:
    connection_str: Optional[str] = os.getenv("AZURE_SERVICE_BUS_CONNECTION_STRING")
    queue_name: Optional[str] = os.getenv("AZURE_SERVICE_BUS_QUEUE_NAME")

    if not connection_str or not queue_name or ServiceBusClient is None:
        # Dev fallback loop
        while True:
            print("worker: Service Bus not configured; sleeping...", flush=True)
            time.sleep(5)
        return

    with ServiceBusClient.from_connection_string(connection_str) as client:
        receiver = client.get_queue_receiver(queue_name)
        with receiver:
            while True:
                for msg in receiver.receive_messages(max_message_count=5, max_wait_time=5):
                    try:
                        body = json.loads(str(msg))
                    except Exception:
                        body = {"raw": str(msg)}
                    process_message(body)
                    receiver.complete_message(msg)


if __name__ == "__main__":
    main()



