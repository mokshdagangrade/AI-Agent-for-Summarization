from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from agent import run_agent, extract_final_answer
from utils import DATA, HOSTS_BY_IP

app = FastAPI(title="Censys Summarizer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)



@app.get("/hosts")
def get_hosts():
    return [
        {
            "ip": h["ip"],
            "location": h.get("location", {}),
            "risk": h.get("threat_intelligence", {}).get("risk_level"),
        }
        for h in DATA["hosts"]
    ]

@app.get("/hosts/{ip}")
def get_host(ip: str):
    host = HOSTS_BY_IP.get(ip)
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")
    return host

@app.post("/qa-global")
def qa_global(payload: dict = Body(...)):
    question = payload.get("question")
    if not question:
        raise HTTPException(status_code=400, detail="Question is required")
    answer = run_agent(question)
    answer_only = extract_final_answer(answer)
    return {"question": question, "answer": answer_only}

@app.get("/summarize-dataset")
def summarize_dataset():
    question = "Please generate a detailed summary of the entire host scan dataset. Include statistical analysis, patterns, feature relationships, and key insights."
    summary = run_agent(question)
    summary_only = extract_final_answer(summary)
    return {"summary": summary_only}

@app.get("/summarize-host/{ip}")
def summarize_host_agent(ip: str):
    if ip not in HOSTS_BY_IP:
        raise HTTPException(status_code=404, detail="Host not found")
    
    question = f"Please generate a detailed, professional summary of the host with IP {ip}. Include risk, services, vulnerabilities, malware, and any notable patterns."
    summary = run_agent(question)
    summary_only = extract_final_answer(summary)
    return {"ip": ip, "summary": summary_only}
