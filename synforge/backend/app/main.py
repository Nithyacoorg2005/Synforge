from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import pandas as pd
import uuid
import os

# Internal SynForge Core Modules
from app.core.reporter import SynForgeReporter
from app.core.generator import SynForgeGenerator
from app.core.evaluator import get_fidelity_report, run_tstr_benchmark 
from app.core.privacy import calculate_membership_leakage

app = FastAPI(title="SynForge API: Privacy-Preserving Data Engine")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job store
jobs = {}

def process_data_task(job_id: str, file_path: str, epsilon: float):
    try:
        # 1. LOAD DATA: Handle stray commas and noisy formatting
        print(f"[SynForge] Loading dataset for job: {job_id}")
        try:
            df = pd.read_csv(file_path, on_bad_lines='skip', quotechar='"', skipinitialspace=True)
        except Exception as load_error:
            print(f"[SynForge] CSV Load Error: {load_error}")
            jobs[job_id] = {"status": "failed", "error": f"Invalid CSV format: {str(load_error)}"}
            return

        # 2. SECURITY LAYER: Identity Stripping
        id_cols = [col for col in df.columns if 'id' in col.lower() or 'roll' in col.lower()]
        fingerprint_cols = [col for col in df.columns if df[col].nunique() == len(df) and col not in id_cols]
        
        to_drop = id_cols + fingerprint_cols
        if to_drop:
            print(f"[SynForge] Security Layer: Dropping identity columns {to_drop}")
            df = df.drop(columns=to_drop)

        # 3. SYNTHESIS: Train and Generate
        engine = SynForgeGenerator()
        engine.train(df, enforce_privacy=True, epsilon=epsilon)
        synthetic_df = engine.generate(num_rows=len(df))
        
        # 4. PERSISTENCE: Save Synthetic File
        syn_path = f"data/synthetic/{job_id}.csv"
        os.makedirs("data/synthetic", exist_ok=True)
        synthetic_df.to_csv(syn_path, index=False)
        
        # 5. AUDIT: Privacy and Fidelity
        privacy_risk = calculate_membership_leakage(df, synthetic_df)
        fidelity_score = get_fidelity_report(df, synthetic_df, engine.metadata)
        
        # 6. BENCHMARK: TSTR Logic
        target = df.columns[-1]
        tstr_data = run_tstr_benchmark(df, synthetic_df, target_col=target)
        
        # 7. FINALIZE
        jobs[job_id] = {
            "status": "completed",
            "fidelity": fidelity_score,
            "privacy_risk": privacy_risk,
            "tstr_results": tstr_data,
            "epsilon": epsilon, 
            "dropped_columns": to_drop,
            "download_url": f"/download/{job_id}"
        }
        print(f"JOB COMPLETED: {job_id} | Risk: {privacy_risk}")

    except Exception as e:
        print(f"TASK ERROR: {e}")
        jobs[job_id] = {"status": "failed", "error": str(e)}

@app.post("/upload")
async def upload_dataset(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...),
    epsilon: float = 0.5 
):
    job_id = str(uuid.uuid4())
    temp_path = f"data/raw/{job_id}.csv"
    os.makedirs("data/raw", exist_ok=True)
    
    with open(temp_path, "wb") as f:
        f.write(await file.read())
    
    jobs[job_id] = {"status": "processing"}
    background_tasks.add_task(process_data_task, job_id, temp_path, epsilon)
    
    return {"job_id": job_id, "message": "Synthesis and validation started."}

@app.get("/status/{job_id}")
async def get_status(job_id: str):
    return jobs.get(job_id, {"error": "Job ID not found"})

@app.get("/download/{job_id}")
async def download_synthetic_file(job_id: str):
    file_path = f"data/synthetic/{job_id}.csv"
    if os.path.exists(file_path):
        return FileResponse(path=file_path, filename=f"synforge_synthetic.csv", media_type='text/csv')
    return {"error": "File not found."}

@app.get("/audit-report/{job_id}")
async def get_audit_report(job_id: str):
    if job_id not in jobs or jobs[job_id]["status"] != "completed":
        return {"error": "Report not ready"}
    
    metrics = jobs[job_id]
    reporter = SynForgeReporter(job_id, metrics)
    report_path = reporter.generate_report()
    
    return FileResponse(path=report_path, filename=f"SynForge_Audit.pdf", media_type='application/pdf')