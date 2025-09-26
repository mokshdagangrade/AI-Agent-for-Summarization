import json
from pathlib import Path
from utils import answer_question_full
from utils import summarize_host

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "hosts_dataset.json"

# Load dataset globally
with open(DATA_PATH) as f:
    DATA = json.load(f)

HOSTS_BY_IP = {h["ip"]: h for h in DATA["hosts"]}


# ACTIONS - Summarize host, QA, Evaluate output

def summarize_host_action(ip: str) -> str:

    host = HOSTS_BY_IP.get(ip)
    if not host:
        return f"Host {ip} not found."

    return summarize_host(host)

def qa_action(question: str) -> str:

    return answer_question_full(DATA, question)

def evaluate_output_action(output: str) -> str:

    feedback = []

    hosts = DATA["hosts"]
    cve_count_map = {}
    service_set = set()
    malware_set = set()
    high_risk_hosts = []

    for h in hosts:
        risk = h.get("threat_intelligence", {}).get("risk_level", "")
        if risk.lower() in ["critical", "high"]:
            high_risk_hosts.append(h["ip"])
        for svc in h.get("services", []):
            service_set.add(f"{svc.get('protocol','')}:{svc.get('port')}")
            for vuln in svc.get("vulnerabilities", []):
                cve = vuln.get("cve_id")
                if cve:
                    cve_count_map[cve] = cve_count_map.get(cve, 0) + 1
        for malware in h.get("threat_intelligence", {}).get("malware_families", []):
            malware_set.add(malware)

    for cve in cve_count_map:
        if cve not in output:
            feedback.append(f"- Missing CVE {cve} affecting {cve_count_map[cve]} hosts")
    for svc in service_set:
        if svc not in output:
            feedback.append(f"- Service {svc} missing from output")
    for malware in malware_set:
        if malware not in output:
            feedback.append(f"- Malware {malware} missing from output")
    if high_risk_hosts:
        feedback.append(f"- High-risk hosts ({len(high_risk_hosts)}): {', '.join(high_risk_hosts)} should be highlighted")

    if not feedback:
        feedback.append("- Output appears complete and consistent with dataset.")

    return "\n".join(feedback)
