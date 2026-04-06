from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import pandas as pd
import uuid
import os
import io
import shutil

# Internal SynForge Core Modules
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

# In-memory job store (Note: This clears on restart. Use Redis for production persistence)
jobs = {}

# Ensure required directories exist
os.makedirs("data/raw", exist_ok=True)
os.makedirs("data/synthetic", exist_ok=True)

def process_data_task(job_id: str, file_path: str, epsilon: float):
    try:
        # 1. LOAD DATA: Handle stray commas and noisy formatting
        print(f"[SynForge] Processing Job: {job_id}")
        try:
            df = pd.read_csv(file_path, on_bad_lines='skip', quotechar='"', skipinitialspace=True)
        except Exception as load_error:
            jobs[job_id] = {"status": "failed", "error": f"Invalid CSV format: {str(load_error)}"}
            return

        # 2. SECURITY LAYER: Identity Stripping
        # Automated ablation of ID-like columns and 100% unique fingerprints
        id_cols = [col for col in df.columns if any(x in col.lower() for x in ['id', 'roll', 'usn', 'email', 'name'])]
        fingerprint_cols = [col for col in df.columns if df[col].nunique() == len(df) and col not in id_cols]
        
        to_drop = list(set(id_cols + fingerprint_cols))
        if to_drop:
            print(f"[SynForge] Security Layer: Dropping {len(to_drop)} identity columns")
            df = df.drop(columns=to_drop)

        # 3. SYNTHESIS: Train and Generate (Uses dynamic tuning from generator.py)
        engine = SynForgeGenerator()
        engine.train(df, enforce_privacy=True, epsilon=epsilon)
        synthetic_df = engine.generate(num_rows=len(df))
        
        # 4. PERSISTENCE: Save Synthetic File
        syn_path = f"data/synthetic/{job_id}.csv"
        synthetic_df.to_csv(syn_path, index=False)
        
        # 5. AUDIT: Privacy and Fidelity
        privacy_risk = calculate_membership_leakage(df, synthetic_df)
        fidelity_score = get_fidelity_report(df, synthetic_df, engine.metadata)
        
        # 6. BENCHMARK: TSTR Logic
        # Heuristic: Use the last column as target if not specified
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
        print(f"[SynForge] SUCCESS: {job_id} | Risk: {privacy_risk}")

    except Exception as e:
        print(f"[SynForge] CRITICAL TASK ERROR: {e}")
        jobs[job_id] = {"status": "failed", "error": "Synthesis failed. Check dataset entropy/formatting."}
    
    finally:
        # Cleanup Raw Data to save disk space on Render
        if os.path.exists(file_path):
            os.remove(file_path)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "engine": "SynForge-V1"}

@app.post("/upload")
async def upload_dataset(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...),
    epsilon: float = 0.5 
):
    # MEMORY GUARD: Limit file size to 1.5MB for Demo Free Tier
    # This prevents the server from crashing during ingestion
    MAX_FILE_SIZE = 1.5 * 1024 * 1024 
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Demo limit is 1.5MB.")

    job_id = str(uuid.uuid4())
    temp_path = f"data/raw/{job_id}.csv"
    
    with open(temp_path, "wb") as f:
        f.write(contents)
    
    jobs[job_id] = {"status": "processing"}
    background_tasks.add_task(process_data_task, job_id, temp_path, epsilon)
    
    return {"job_id": job_id, "message": "Synthesis started. Poll /status/{job_id} for results."}

@app.get("/status/{job_id}")
async def get_status(job_id: str):
    return jobs.get(job_id, {"error": "Job ID not found"})

@app.get("/download/{job_id}")
async def download_synthetic_file(job_id: str):
    file_path = f"data/synthetic/{job_id}.csv"
    if os.path.exists(file_path):
        return FileResponse(path=file_path, filename=f"synforge_{job_id}.csv", media_type='text/csv')
    raise HTTPException(status_code=404, detail="File not found.")
