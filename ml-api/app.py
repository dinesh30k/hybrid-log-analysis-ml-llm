from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import csv
import io
from pydantic import BaseModel
import pickle
import boto3
import uuid
import os
from datetime import datetime
from decimal import Decimal
from dotenv import load_dotenv
import os
import requests
import json
import time

print(" RUNNING FILE:", __file__)

load_dotenv()

model = None
vectorizer = None
table = None
import re

# ============================================
# OLLAMA CONFIGURATION
# ============================================
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama2")
OLLAMA_ENABLED = os.getenv("OLLAMA_ENABLED", "true").lower() == "true"

print(f"🤖 Ollama Config: URL={OLLAMA_BASE_URL}, Model={OLLAMA_MODEL}, Enabled={OLLAMA_ENABLED}")

def clean_log(text):
    text = text.lower()
    text = re.sub(r'\d+', '', text)
    text = re.sub(r'[^a-z\s]', '', text)
    return text.strip()


def predict_level(log_text):
    load_resources()   # 👈 ensures model is loaded
    cleaned = clean_log(log_text)
    vec = vectorizer.transform([cleaned])
    return model.predict(vec)[0]

def load_resources():
    global model, vectorizer, table

    if model is None:
        model = pickle.load(open("model.pkl", "rb"))
        vectorizer = pickle.load(open("vectorizer.pkl", "rb"))

    if table is None:
        dynamodb = boto3.resource(
        "dynamodb",
        region_name="ap-south-2",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("AWS_SECRET_KEY")
    )
        table = dynamodb.Table("log_predictions")


# ============================================
# OLLAMA HELPER FUNCTIONS
# ============================================

def is_ollama_available():
    """Check if Ollama service is running"""
    if not OLLAMA_ENABLED:
        return False
    
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2)
        return response.status_code == 200
    except:
        return False


def call_ollama(prompt: str, max_tokens: int = 500) -> str:
    """
    Call Ollama model for log analysis
    Returns: Response text or error message
    """
    if not OLLAMA_ENABLED or not is_ollama_available():
        return None
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.3,  # Lower temperature for consistency
            },
            timeout=60
        )
        
        elapsed = time.time() - start_time
        print(f"⏱ Ollama response time: {elapsed:.2f}s")
        
        if response.status_code == 200:
            result = response.json().get("response", "").strip()
            return result
        else:
            print(f"❌ Ollama error: {response.status_code}")
            return None
            
    except requests.Timeout:
        print("❌ Ollama timeout")
        return None
    except Exception as e:
        print(f"❌ Ollama error: {str(e)}")
        return None


def analyze_log_with_ollama(log_text: str, ml_prediction: str, ml_confidence: float) -> dict:
    """
    Use Ollama to analyze log when ML confidence is low or for detailed analysis
    """
    if not is_ollama_available():
        return {"error": "Ollama not available"}
    
    prompt = f"""Analyze this system log and classify its severity level.

Log: {log_text}

ML Model Prediction: {ml_prediction} (Confidence: {ml_confidence:.1f}%)

Please respond with ONLY a JSON object (no markdown, no explanation):
{{
    "severity": "CRITICAL|SECURITY|ERROR|WARN|INFO|UNKNOWN",
    "reasoning": "Brief explanation (one sentence)",
    "recommendation": "Suggested action"
}}"""
    
    response = call_ollama(prompt)
    
    if response:
        try:
            import re

            # Extract JSON safely
            match = re.search(r"\{.*\}", response, re.DOTALL)
            if match:
                json_str = match.group()
                result = json.loads(json_str)

                # Validate fields
                result.setdefault("severity", "UNKNOWN")    
                result.setdefault("reasoning", "No reasoning provided")
                result.setdefault("recommendation", "Manual review needed")

                result["source"] = "ollama"
                return result

        except Exception as e:
            print("⚠️ JSON parse failed:", str(e))

        # 👉 fallback (VERY IMPORTANT)
        return {
            "severity": "UNKNOWN",
            "reasoning": response[:300],
            "recommendation": "Could not parse structured output",
            "source": "ollama_raw"
        }

    return {"error": "No response from Ollama"}


def get_ollama_explanation(log_text: str, severity: str) -> str:
    """
    Get detailed explanation from Ollama about why a log is important
    """
    if not is_ollama_available():
        return None
    
    prompt = f"""Explain in 2-3 sentences why this system log is important for system administrators.

Log: {log_text}
Severity: {severity}

Be concise and practical."""
    
    return call_ollama(prompt, max_tokens=200)


def generate_ollama_summary(logs: list) -> str:
    """
    Generate comprehensive system summary using Ollama
    """
    if not is_ollama_available() or not logs:
        return None
    
    # Prepare log summaries
    log_summary = "\n".join([
        f"- {log.get('log', '')[:80]} → {log.get('prediction', 'UNKNOWN')}"
        for log in logs[:15]
    ])
    
    prompt = f"""You are a senior system monitoring expert. Analyze these recent system logs and provide:
1. Top 3 issues identified
2. Immediate actions needed
3. Risk level (Low/Medium/High/Critical)

Recent Logs:
{log_summary}

Respond in plain text, no bullet points formatting needed."""
    
    return call_ollama(prompt, max_tokens=400)


from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all (safe for now)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LogRequest(BaseModel):
    log: str
    use_ollama: bool = False  # Optional: force Ollama analysis


@app.post("/predict")
def predict_log(request: LogRequest):
    load_resources()
    try:
        log_text = request.log
        print("📥 Incoming log:", log_text)

        cleaned = clean_log(log_text)   # 🔥 IMPORTANT

        X = vectorizer.transform([cleaned])
        prediction = model.predict(X)[0]
        probs = model.predict_proba(X)[0]

        confidence = float(max(probs)) * 100
        labels = model.classes_

        # Top 2 predictions safely
        sorted_indices = probs.argsort()[::-1]
        top_preds = []

        for i in sorted_indices[:2]:
            top_preds.append({
                "label": labels[i],
                "confidence": float(probs[i]) * 100
            })

        # ============================================
        # OLLAMA FALLBACK LOGIC
        # ============================================
        ollama_result = None
        prediction_source = "ml_model"
        
        if request.use_ollama or confidence < 25:
            print(f"🤖 Confidence too low ({confidence:.1f}%) or forced Ollama - using Ollama for analysis")
            ollama_result = analyze_log_with_ollama(log_text, prediction, confidence)
            
            if ollama_result and "severity" in ollama_result:
                prediction = ollama_result["severity"]
                confidence = 95.0  # High confidence from LLM analysis
                prediction_source = "ollama_analysis"
                print(f"✅ Ollama decision: {prediction}")
        
        if confidence < 25:
            prediction = "UNKNOWN"
            
        valid_labels = ["CRITICAL", "SECURITY", "ERROR", "WARN", "INFO", "UNKNOWN"]

        if prediction not in valid_labels:
            prediction = "UNKNOWN"


        item = {
            "id": str(uuid.uuid4()),
            "log": log_text,
            "prediction": prediction,
            "confidence": Decimal(str(confidence)),
            "timestamp": datetime.utcnow().isoformat(),
            "prediction_source": prediction_source,  # Track which system made the prediction
            "ollama_analysis": ollama_result if ollama_result else None
        }

        table.put_item(Item=item)

        print("Stored in DynamoDB")

     
        return {
            "prediction": prediction,
            "confidence": confidence,
            "top_predictions": top_preds,
            "prediction_source": prediction_source,
            "ollama_analysis": ollama_result,
            "stored_in_db": True
        }

    except Exception as e:
        print("ERROR:", str(e))
        return {
            "error": str(e),
            "stored_in_db": False
        }

        
        
from fastapi import Query

@app.get("/logs")
def get_logs(
    limit: int = 50,
    search: str = "",
    level: str = "ALL",
    startDate: str = "",
    endDate: str = ""
):
    load_resources()
    try:
        response = table.scan()
        items = response.get("Items", [])
        
        filtered = []

        for item in items:
            log_text = str(item.get("log", "")).lower()
            clean_search = str(search).strip().lower()
            log_text = item.get("log", "")

            prediction = item.get("prediction", "UNKNOWN")
                
            timestamp = item.get("timestamp", "")

            # SEARCH FILTER
            if clean_search and clean_search not in log_text:
                continue

            # LEVEL FILTER
            if level != "ALL" and prediction != level:
                continue

            # DATE FILTER
            if timestamp:
                log_date = datetime.fromisoformat(timestamp)

                if startDate:
                    start = datetime.fromisoformat(startDate)
                    if log_date < start:
                        continue

                if endDate:
                    end = datetime.fromisoformat(endDate)
                    if log_date > end:
                        continue

            filtered.append({
                "log": item.get("log", ""),
                "prediction": prediction,
                "confidence": item.get("confidence", 0),
                "timestamp": timestamp
            })

        items = filtered

        # Sort latest first
        items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        # Apply limit AFTER sorting
        items = items[:limit]

        return {"logs": items}

    except Exception as e:
        return {"error": str(e)}

def compute_counts(items):
    counts = {
        "CRITICAL": 0,
        "ERROR": 0,
        "SECURITY": 0,
        "WARN": 0,
        "INFO": 0,
        "UNKNOWN": 0
    }

    for item in items:
        pred = item.get("prediction", "UNKNOWN")
        if pred in counts:
            counts[pred] += 1
        else:
            counts["UNKNOWN"] += 1

    return counts

    
@app.get("/insights")
def get_insights():

    print("NEW INSIGHTS FUNCTION RUNNING")
    load_resources()

    try:
        response = table.scan()
        all_items = response.get("Items", [])
        total_all = len(all_items)

        latest_items = sorted(
            all_items,
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )[:50]

        total = len(latest_items)

        if total == 0:
            return {"insights": "No logs available."}

        counts = compute_counts(latest_items)

        # Percentages
        percentages = {
            key: (value / total) * 100
            for key, value in counts.items()
        }

        # ALWAYS define before use
        security_pct = percentages.get("SECURITY", 0)
        critical_pct = percentages.get("CRITICAL", 0)
        unknown_pct = percentages.get("UNKNOWN", 0)

        # Insight logic
        insights = []

        if security_pct > 25:
            insights.append("⚠️ High SECURITY logs detected")

        if critical_pct > 10:
            insights.append("🚨 Critical errors present — check system stability")

        if unknown_pct > 30:
            insights.append("❓ Many UNKNOWN logs — model confidence may be low")                           

        if not insights:
            insights.append("✅ System appears normal")

        return {
            "counts": counts,
            "percentages": percentages,
            "insights": "<br>".join(insights),
            "total_all": total_all,
            "total_recent": total
        }

    except Exception as e:
        return {"error": str(e)}
    
# ================= AI SUMMARY FUNCTION =================

def generate_ai_summary(logs):
    if not logs:
        return "No logs available." 

    recent_logs = logs[:20]

    log_text = "\n".join([
        f"{l.get('log')} -> {l.get('prediction')}"
        for l in recent_logs
    ])

    prompt = f"""
You are a professional system monitoring AI.

Analyze the logs below and respond ONLY in this format:

Main Issues:
- ...

Severity:
- Low / Medium / High

Recommended Actions:
- ...

IMPORTANT:
- Do NOT tell stories
- Do NOT imagine scenarios
- Do NOT explain unrelated things
- Keep response short and clear

Logs:
{log_text}
"""

    # Use Ollama if available
    if is_ollama_available():
        result = call_ollama(prompt)
        if result:
            return result
    
    # Fallback to direct HTTP call (old method)
    try:
        import time

        start = time.time()

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "phi",
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )

        print("📡 AI status code:", response.status_code)
        print("⏱ AI response time:", round(time.time() - start, 2), "seconds")

        return response.json()["response"]

    except Exception as e:
        print("❌ AI ERROR:", str(e))  
        return "⚠️ AI summary unavailable (model slow or not running)"

# ================= AI SUMMARY API =================

@app.get("/ai-summary")
def get_ai_summary():
    load_resources()
    try:
        response = table.scan()
        logs = response.get("Items", [])

        summary = generate_ai_summary(logs)

        return {"summary": summary}
    except:
        return {"summary": "Error generating AI summary"}
    
@app.get("/smart-filters")
def get_smart_filters():
    load_resources()
    try:
        response = table.scan()
        all_items = response.get("Items", [])

        # single source of truth
        latest_items = sorted(
            all_items,
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )[:50]      

        if not latest_items:
            return {"suggestions": []}

        
        # ===============================
        # STEP 1: COUNT PREDICTIONS (ML BASED)
        counts = compute_counts(latest_items)

        total_logs = len(latest_items)
        print("SMART FILTER COUNTS:", counts)
        print("TOTAL LOGS:", total_logs)
        
        if total_logs == 0:
            return {"suggestions": []}
        
        suggestions = []
        
        
        log_texts = " ".join([
            str(item.get("log", "")).lower()
            for item in latest_items
        ])

        # ===============================
        # STEP 2: GENERATE SUGGESTIONS
        # ===============================
        percentages = {
            key: (value / total_logs) * 100
            for key, value in counts.items()
        }
        

        for level, percentage in percentages.items():       

            # Only suggest if significant (>30%)
            if percentage > 30:
                suggestions.append({
                    "type": "filter",
                    "value": level,
                    "message": f"⚠️ {level} logs are high ({percentage:.1f}%)"
                })
        


        # ================================
        # STEP 2B: KEYWORD INTELLIGENCE
        # ================================

   
        # ================================
        # CLEAN DUPLICATE SUGGESTIONS
        # ================================

        seen = set()
        cleaned = []

        for s in suggestions:
            key = (s["type"], s["value"])
            if key not in seen:
                cleaned.append(s)
                seen.add(key)

        suggestions = cleaned
        
        # =========================
        # AGENT ACTION LAYER (NEW)
        # =========================

        action_suggestions = []

        for s in suggestions:
            # ML-based filters
            if s["type"] == "filter":
                level = s["value"]

                if level == "CRITICAL":
                    action_suggestions.append({
                        "type": "action",
                        "value": "investigate_critical",
                        "message": "🚨 Immediate attention required: Investigate CRITICAL errors"
                    })

                elif level == "ERROR":
                    action_suggestions.append({
                        "type": "action",
                        "value": "check_errors",
                        "message": "⚠️ Review error logs to prevent system failure"
                    })

                elif level == "SECURITY":
                    action_suggestions.append({
                        "type": "action",
                        "value": "audit_security",
                        "message": "🔐 Check authentication & access control"
                    })

            # Keyword-based patterns
            elif s["type"] == "search":
                keyword = s["value"]

                if keyword == "memory":
                    action_suggestions.append({
                        "type": "action",
                        "value": "check_memory",
                        "message": "🧠 Monitor memory usage and optimize resources"
                    })

                elif keyword == "disk":
                    action_suggestions.append({
                        "type": "action",
                        "value": "check_disk",
                        "message": "💾 Check disk space and cleanup if needed"
                    })

                elif keyword == "unauthorized":
                    action_suggestions.append({
                        "type": "action",
                        "value": "security_alert",
                        "message": "🔒 Investigate unauthorized access attempts"
                    })

        # Merge actions into suggestions
        suggestions.extend(action_suggestions)      

        # =========================
        # AGENT PRIORITIZATION
        # =========================
        priority_order = ["CRITICAL", "ERROR", "SECURITY", "WARN", "INFO", "UNKNOWN"]

        suggestions.sort(
            key=lambda s: priority_order.index(s["value"])
            if s["type"] == "filter" and s["value"] in priority_order
            else 999
        )


        return {"suggestions": suggestions}


    except Exception as e:
        return {"error": str(e)}

# ============================================
# OLLAMA INTEGRATION ENDPOINTS
# ============================================

@app.get("/ollama/status")
def get_ollama_status():
    """Check if Ollama is available and working"""
    available = is_ollama_available()
    
    return {
        "ollama_enabled": OLLAMA_ENABLED,
        "ollama_available": available,
        "ollama_url": OLLAMA_BASE_URL,
        "ollama_model": OLLAMA_MODEL,
        "status": "✅ Online" if available else "❌ Offline"
    }


class AnalysisRequest(BaseModel):
    log: str
    detailed: bool = False


@app.post("/ollama/analyze")
def ollama_analyze(request: AnalysisRequest):
    """
    Pure Ollama analysis of a log (bypasses ML model)
    Returns detailed analysis and recommendations
    """
    if not is_ollama_available():
        return {"error": "Ollama service is not available"}
    
    log_text = request.log
    result = analyze_log_with_ollama(log_text, "UNKNOWN", 0)
    
    # Add detailed explanation if requested
    if request.detailed and result and "severity" in result:
        explanation = get_ollama_explanation(log_text, result["severity"])
        if explanation:
            result["detailed_explanation"] = explanation
    
    return result


@app.post("/ollama/compare")
def ollama_compare(request: LogRequest):
    """
    Compare ML model prediction with Ollama analysis
    Returns both predictions for user decision
    """
    load_resources()
    
    try:
        log_text = request.log
        cleaned = clean_log(log_text)
        
        # ML prediction
        X = vectorizer.transform([cleaned])
        ml_pred = model.predict(X)[0]
        ml_probs = model.predict_proba(X)[0]
        ml_confidence = float(max(ml_probs)) * 100
        
        # Ollama prediction
        ollama_result = analyze_log_with_ollama(log_text, ml_pred, ml_confidence)
        
        return {
            "log": log_text,
            "ml_prediction": {
                "severity": ml_pred,
                "confidence": ml_confidence
            },
            "ollama_prediction": ollama_result,
            "recommendation": "Use Ollama if confidence differs significantly or for critical logs"
        }
    
    except Exception as e:
        return {"error": str(e)}


@app.get("/ollama/summary")
def ollama_summary():
    """Generate comprehensive system summary using Ollama"""
    load_resources()
    
    if not is_ollama_available():
        return {"error": "Ollama service is not available"}
    
    try:
        response = table.scan()
        logs = response.get("Items", [])
        
        if not logs:
            return {"summary": "No logs available for analysis"}
        
        latest_logs = sorted(
            logs,
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )[:20]
        
        summary = generate_ollama_summary(latest_logs)
        
        if summary:
            return {"summary": summary, "logs_analyzed": len(latest_logs)}
        else:
            return {"error": "Failed to generate summary"}
    
    except Exception as e:
        return {"error": str(e)}


@app.post("/ollama/batch-analyze")
def ollama_batch_analyze(logs_list: list):
    """
    Analyze multiple logs using Ollama
    Returns analysis for each log
    """
    if not is_ollama_available():
        return {"error": "Ollama service is not available"}
    
    results = []
    
    for log_text in logs_list[:10]:  # Limit to 10 for performance
        analysis = analyze_log_with_ollama(log_text, "UNKNOWN", 0)
        results.append({
            "log": log_text[:100],  # Truncate for response
            "analysis": analysis
        })
    
    return {
        "total_analyzed": len(results),
        "results": results
    }


@app.get("/ollama/explain/{log_id}")
def ollama_explain(log_id: str):
    """Get detailed Ollama explanation for a specific stored log"""
    load_resources()
    
    if not is_ollama_available():
        return {"error": "Ollama service is not available"}
    
    try:
        response = table.get_item(Key={"id": log_id})
        
        if "Item" not in response:
            return {"error": "Log not found"}
        
        item = response["Item"]
        log_text = item.get("log", "")
        severity = item.get("prediction", "UNKNOWN")
        
        explanation = get_ollama_explanation(log_text, severity)
        
        return {
            "log_id": log_id,
            "log": log_text,
            "severity": severity,
            "explanation": explanation
        }
    
    except Exception as e:
        return {"error": str(e)}
    
@app.get("/export/csv")
def export_csv():
    load_resources()
    try:
        response = table.scan()
        items = response.get("Items", [])

        # same dataset logic (IMPORTANT)
        latest_items = sorted(
            items,
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )[:50]

        # create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # header
        writer.writerow(["log", "prediction", "confidence", "timestamp"])

        # rows
        for item in latest_items:
            writer.writerow([
                item.get("log", ""),
                item.get("prediction", ""),
                item.get("confidence", ""),
                item.get("timestamp", "")
            ])

        output.seek(0)

        return StreamingResponse(
            output,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=logs.csv"}
        )

    except Exception as e:
        return {"error": str(e)}
    
@app.get("/export/json")
def export_json():
    load_resources()   # IMPORTANT

    try:
        response = table.scan()
        items = response.get("Items", [])

        latest_items = sorted(
            items,
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )[:50]

        return {
            "logs": latest_items
        }

    except Exception as e:
        return {"error": str(e)}
    
@app.get("/alerts")
def get_alerts():
    load_resources()

    try:
        response = table.scan()
        items = response.get("Items", [])

        latest_items = sorted(
            items,
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )[:50]

        alerts = detect_alerts(latest_items)

        return {"alerts": alerts}

    except Exception as e:
        return {"error": str(e)}
    
@app.get("/export/summary")
def export_summary():
    load_resources()

    try:
        response = table.scan()
        items = response.get("Items", [])

        latest_items = sorted(
            items,
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )[:50]

        # reuse your existing logic
        counts = compute_counts(latest_items)
        total = len(latest_items)

        if total == 0:
            return {"summary": "No logs available."}

        percentages = {
            key: (value / total) * 100
            for key, value in counts.items()
        }

        # extract values
        security_pct = percentages.get("SECURITY", 0)
        critical_pct = percentages.get("CRITICAL", 0)
        error_pct = percentages.get("ERROR", 0)
        unknown_pct = percentages.get("UNKNOWN", 0)

        # AI-style summary (clean + natural)
        summary = []

        if security_pct > 25:
            summary.append(f"High number of security-related events ({security_pct:.1f}%).")

        if critical_pct > 10:
            summary.append(f"Critical system issues detected ({critical_pct:.1f}%).")

        if error_pct > 15:
            summary.append(f"Frequent error occurrences observed ({error_pct:.1f}%).")

        if unknown_pct > 30:
            summary.append("Significant portion of logs are unclear, model confidence may be low.")

        if not summary:
            summary.append("System is operating within normal parameters.")

        return {
            "summary": " ".join(summary)
        }

    except Exception as e:
        return {"error": str(e)}
    
def detect_alerts(items):
    counts = compute_counts(items)
    total = len(items)

    if total == 0:
        return []

    percentages = {
        k: (v / total) * 100
        for k, v in counts.items()
    }

    alerts = []

    # 🔴 CRITICAL ALERT
    if percentages.get("CRITICAL", 0) > 10:
        alerts.append({
            "level": "CRITICAL",
            "message": "🚨 High number of CRITICAL logs detected",
            "priority": 1
        })

    # 🟠 ERROR ALERT
    if percentages.get("ERROR", 0) > 15:
        alerts.append({
            "level": "ERROR",
            "message": "⚠️ Error rate is high",
            "priority": 2
        })

    # 🔐 SECURITY ALERT
    if percentages.get("SECURITY", 0) > 25:
        alerts.append({
            "level": "SECURITY",
            "message": "🔐 Possible security risks detected",
            "priority": 3
        })

    # ❓ UNKNOWN ALERT
    if percentages.get("UNKNOWN", 0) > 30:
        alerts.append({
            "level": "UNKNOWN",
            "message": "❓ Many unknown logs — model may be uncertain",
            "priority": 4
        })

    return sorted(alerts, key=lambda x: x["priority"])

def detect_anomalies(items):
    if len(items) < 20:
        return []

    mid = len(items) // 2
    recent = items[:mid]
    older = items[mid:]

    recent_counts = compute_counts(recent)
    older_counts = compute_counts(older)

    anomalies = []

    recent_total = len(recent)
    older_total = len(older)

    for level in ["CRITICAL", "ERROR", "SECURITY"]:
        recent_pct = (recent_counts.get(level, 0) / recent_total) * 100 if recent_total else 0
        older_pct = (older_counts.get(level, 0) / older_total) * 100 if older_total else 0

        if older_pct == 0 and recent_pct > 10:
            anomalies.append({
                "type": "spike",
                "level": level,
                "message": f"🚨 Sudden spike in {level} logs (was 0%, now {recent_pct:.1f}%)"
            })

        elif recent_pct - older_pct > 15:
            anomalies.append({
                "type": "spike",
                "level": level,
                "message": f"📈 {level} logs increased ({older_pct:.1f}% → {recent_pct:.1f}%)"
            })

    return anomalies

@app.get("/alerts/ai")
def get_ai_alerts():
    load_resources()

    try:
        response = table.scan()
        items = response.get("Items", [])

        latest_items = sorted(
            items,
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )[:50]

        anomalies = detect_anomalies(latest_items)

        return {"ai_alerts": anomalies}

    except Exception as e:
        return {"error": str(e)}