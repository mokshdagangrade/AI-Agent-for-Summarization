import re
from openai import OpenAI
from pathlib import Path
import json
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "hosts_dataset.json"

with open(DATA_PATH) as f:
    DATA = json.load(f)

HOSTS_BY_IP = {h["ip"]: h for h in DATA["hosts"]}

load_dotenv()
api_key = os.getenv("HF_API_KEY")

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=api_key,
)

def host_to_text(host: dict) -> str:
    lines = []
    lines.append(f"**Host IP:** {host.get('ip', 'unknown')}")
    loc = host.get("location", {})
    lines.append(f"- Location: {loc.get('city','unknown')}, {loc.get('country','unknown')}")
    risk = host.get("threat_intelligence", {}).get("risk_level", "unknown")
    lines.append(f"- Overall Risk Level: *{risk}*")

    malware = host.get("threat_intelligence", {}).get("malware_families", [])
    if malware:
        lines.append(f"- Detected Malware: {', '.join(malware)}")

    for svc in host.get("services", []):
        svcline = f"- Service: {svc.get('protocol','')} on port {svc.get('port','unknown')}"
        vulns = svc.get("vulnerabilities", [])
        if vulns:
            vuln_list = ", ".join([v["cve_id"] for v in vulns])
            svcline += f" (Vulnerabilities: {vuln_list})"
        if svc.get("authentication_required"):
            svcline += " (Authentication Required)"
        if svc.get("malware_detected"):
            svcline += f" (Malware: {svc['malware_detected']['name']})"
        lines.append(svcline)

    lines.append("- Recommendation: Patch critical/high vulnerabilities and restrict remote access.")
    return "\n".join(lines)

def summarize_host(host: dict, max_length=180, min_length=80) -> str:
    host_text = host_to_text(host)
    prompt =f"""
    You are a cybersecurity analyst. You are given a dataset in JSON format containing host scan results. 

    Your tasks are:
    1. **Dataset Summary**: Provide a clear, structured, and detailed summary of the dataset. Break down by:
    - Number of hosts scanned
    - Geographic distribution (cities, countries)
    - Risk level distribution (critical, high, medium, low, unknown)
    - Services exposed (protocols, ports)
    - Vulnerabilities (group by CVE, count how many hosts are affected)
    - Malware detections (families, frequency)

    2. **Statistical Analysis**: Perform quantitative analysis, including:
    - Counts and percentages (e.g., "% of hosts with SSH exposed", "% of hosts with high risk")
    - Top N vulnerabilities (by occurrence across hosts)
    - Top N services exposed
    - Any concentration of risks in specific IPs, ports, or locations

    3. **Key Findings & Insights**: Highlight the most important and actionable points:
    - Which services or vulnerabilities represent the biggest threat
    - Which hosts need immediate attention
    - Patterns (e.g., all high-risk hosts in a certain location, repeated CVEs across many hosts)
    - Any anomalies or unusual activity

    4. **Output Format**:
    - Use **bullet points** and **Markdown headings** for clarity
    - Organize into sections: *Summary, Statistics, Key Findings, Recommendations*
    - Be precise, concise, and professional

    Data:
    {host_text}

    Answer:

    """
    result = client.chat.completions.create(
        model="mistralai/Mistral-7B-Instruct-v0.2:featherless-ai",
        messages=[{"role":"user", "content": prompt}]
    )
    summary = result.choices[0].message

    # Highlight IPs and CVEs in bold
    summary = re.sub(r"(\b\d{1,3}(?:\.\d{1,3}){3}\b)", r"**\1**", summary)
    summary = re.sub(r"(CVE-\d{4}-\d{4,7})", r"**\1**", summary)
    return summary

def answer_question_full(dataset: dict, question: str, max_length=200, min_length=20) -> str:
    context = ""
    for host in dataset["hosts"]:
        context += host_to_text(host) + "\n\n"

    prompt = f"""
    You are a cybersecurity analyst. Answer the question based on the dataset below. Be concise and structured using Markdown.

    Dataset:
    {context}

    Question: {question}
    Answer:
    """
    result = client.chat.completions.create(
        model="mistralai/Mistral-7B-Instruct-v0.2:featherless-ai",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
    )
    return result.choices[0].message
