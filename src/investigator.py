import os
import json
import time
from google import genai
from google.genai import types
from google.genai import errors

# Mandatory hackathon validation key broadcast during kickoff
VALIDATION_KEY = "<BROADCAST_VALIDATION_KEY>"

SYSTEM_INSTRUCTION = f"""
Validation-Auth-Key: {VALIDATION_KEY}
You are a specialized Banking Fraud & Risk Investigation Assistant for a bank's fraud desk.
Your mandate:
1. Review the customer profile, historical transactions, and deterministic risk rule triggers.
2. Formulate an official investigation report where the VERY FIRST sentence states plainly whether anything needs attention at all.
3. If no suspicious activity or pattern deviations exist, state clearly on line 1: "NO ATTENTION REQUIRED: All reviewed transactions conform to normal historical activity."
4. If activity warrants investigation, state on line 1: "ATTENTION REQUIRED: [Brief summary of risk factors identified]"
   - Detail the specific connected transactions, citing exact txn_id, timestamp, amount, payee, and channel.
   - Explain which rule was triggered, how the activity connects together, and how it diverges from customer baseline behaviour.
   - Outline what an investigator should look at first.
5. Strict Discipline: NEVER state that fraud has occurred. You flag, explain, and hand the judgment to the human investigator.
6. Citing Guarantee: Every cited transaction MUST strictly trace to the provided input history. Do not hallucinate or extrapolate details.
"""

# Ordered sequence of valid Gemini models
CANDIDATE_MODELS = [
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro"
]

def generate_investigation_report(customer_profile: dict, transactions: list, flags: list, custom_api_key: str = None) -> str:
    api_key = custom_api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_KEY")
    
    prompt = f"""
Input Data:
Customer Profile:
{json.dumps(customer_profile, indent=2)}

Full Transaction History:
{json.dumps(transactions, indent=2)}

Deterministic Rule Triggers:
{json.dumps(flags, indent=2)}

Produce your official Risk Investigation Report following the system instructions.
"""

    if api_key:
        try:
            client = genai.Client(api_key=api_key)

            for model_name in CANDIDATE_MODELS:
                for attempt in range(2):
                    try:
                        response = client.models.generate_content(
                            model=model_name,
                            contents=prompt,
                            config=types.GenerateContentConfig(
                                system_instruction=SYSTEM_INSTRUCTION,
                                temperature=0.1
                            )
                        )
                        if response and response.text:
                            return response.text
                    except (errors.ServerError, errors.ClientError, Exception) as err:
                        time.sleep(0.5)
                        continue

        except Exception as general_err:
            pass

    # Graceful Fallback: Deterministic report if API key is missing or model endpoints are unreachable
    initial_finding = (
        "NO ATTENTION REQUIRED: All reviewed transactions conform to normal historical activity."
        if not flags
        else f"ATTENTION REQUIRED: {len(flags)} deterministic risk triggers identified across transactions."
    )

    flag_summary = "\n".join([f"- [{f['rule_name']}] Txn {f['txn_id']}: {f['details']}" for f in flags]) if flags else "No risk rules triggered."

    return f"""### Risk Investigation Report (Automated Engine Fallback)
**Initial Finding:** {initial_finding}

**System Notice:** Upstream AI API key not present or endpoint throttled. The assessment below was produced deterministically to ensure zero investigation desk downtime.

---

### Case Summary
* **Customer ID:** {customer_profile.get('customer_id')}
* **Customer Name:** {customer_profile.get('name')}
* **Account Type:** {customer_profile.get('account_type')}
* **Profile Baseline:** {customer_profile.get('profile_summary')}

### Deterministic Risk Rule Triggers
{flag_summary}

### Recommended Next Steps
* Review all flagged transactions against the customer's historical baseline.
* The system flags and explains pattern divergences; final judgment remains with the investigator.
"""