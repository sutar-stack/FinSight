"""
FinSight Backend - Flask API
Handles SMS parsing, transaction categorization, and AI coaching via Gemini
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import re
import json
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173", "http://localhost:3000", "*"])

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
else:
    model = None

# ─────────────────────────────────────────────────
# SMS PARSER
# ─────────────────────────────────────────────────

DEBIT_PATTERNS = [
    r"(?:debited|deducted|spent|paid|withdrawn|INR|Rs\.?|₹)\s*[:\-]?\s*([\d,]+(?:\.\d{1,2})?)",
    r"([\d,]+(?:\.\d{1,2})?)\s*(?:debited|deducted|spent)",
]

CREDIT_PATTERNS = [
    r"(?:credited|received|deposited)\s*(?:with\s*)?(?:INR|Rs\.?|₹)?\s*([\d,]+(?:\.\d{1,2})?)",
    r"([\d,]+(?:\.\d{1,2})?)\s*(?:credited|received)",
]

MERCHANT_PATTERNS = [
    r"(?:at|to|from|paid to|payment to)\s+([A-Z][A-Za-z0-9\s&\.\-']{2,40}?)(?:\s+on|\s+via|\s+ref|\s+for|\.|,|$)",
    r"(?:UPI|NEFT|IMPS|transfer to)\s+([A-Z][A-Za-z0-9\s&\.\-']{2,40}?)(?:\s+on|\s+via|\s+ref|\.|,|$)",
]

DATE_PATTERNS = [
    r"(\d{2}[-/]\d{2}[-/]\d{2,4})",
    r"(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*\d{0,4})",
    r"(\d{2}[A-Z][a-z]{2}\d{4})",
]

BALANCE_PATTERNS = [
    r"(?:balance|bal\.?|avl\.?\s*bal)\s*(?:is\s*)?(?:INR|Rs\.?|₹)?\s*[:=]?\s*([\d,]+(?:\.\d{1,2})?)",
]

UPI_PATTERN = r"(?:UPI|upi)\s*(?:Ref\.?\s*(?:No\.?)?\s*|ID\s*:?\s*)(\d{6,20})"
REF_PATTERN = r"(?:Ref\.?\s*(?:No\.?)?\s*|txn\s*(?:id|no)\.?\s*:?\s*)([A-Z0-9]{6,20})"


def extract_amount(text):
    """Extract transaction amount from SMS text."""
    for pattern in DEBIT_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            raw = m.group(1).replace(",", "")
            try:
                return float(raw)
            except ValueError:
                continue
    return None


def detect_transaction_type(text):
    """Detect if SMS is debit or credit."""
    text_lower = text.lower()
    debit_keywords = ["debited", "deducted", "spent", "paid", "withdrawn", "payment", "purchase"]
    credit_keywords = ["credited", "received", "deposited", "refund", "cashback"]
    
    debit_score = sum(1 for kw in debit_keywords if kw in text_lower)
    credit_score = sum(1 for kw in credit_keywords if kw in text_lower)
    
    if credit_score > debit_score:
        return "credit"
    return "debit"


def extract_merchant(text):
    """Extract merchant name from SMS."""
    for pattern in MERCHANT_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            merchant = m.group(1).strip()
            if len(merchant) > 2:
                return merchant.title()
    return "Unknown Merchant"


def extract_date(text):
    """Extract transaction date from SMS."""
    for pattern in DATE_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            raw = m.group(1).strip()
            for fmt in ["%d-%m-%Y", "%d/%m/%Y", "%d-%m-%y", "%d/%m/%y",
                        "%d %b %Y", "%d %b", "%d%b%Y"]:
                try:
                    dt = datetime.strptime(raw, fmt)
                    if dt.year == 1900:
                        dt = dt.replace(year=datetime.now().year)
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    continue
            return raw
    return datetime.now().strftime("%Y-%m-%d")


def extract_balance(text):
    """Extract available balance from SMS."""
    for pattern in BALANCE_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            raw = m.group(1).replace(",", "")
            try:
                return float(raw)
            except ValueError:
                pass
    return None


def extract_reference(text):
    """Extract UPI/reference ID."""
    m = re.search(UPI_PATTERN, text, re.IGNORECASE)
    if m:
        return "UPI:" + m.group(1)
    m = re.search(REF_PATTERN, text, re.IGNORECASE)
    if m:
        return m.group(1)
    return None


def parse_sms(sms_text):
    """Parse a single Indian bank SMS into structured transaction data."""
    sms_text = sms_text.strip()
    
    # Skip non-transaction SMS
    non_tx_keywords = ["otp", "password", "login", "alert: your", "dear customer, your account"]
    text_lower = sms_text.lower()
    for kw in non_tx_keywords:
        if kw in text_lower and "debited" not in text_lower and "credited" not in text_lower:
            return None
    
    amount = extract_amount(sms_text)
    if amount is None or amount <= 0:
        return None

    return {
        "raw": sms_text,
        "amount": amount,
        "type": detect_transaction_type(sms_text),
        "merchant": extract_merchant(sms_text),
        "date": extract_date(sms_text),
        "balance": extract_balance(sms_text),
        "reference": extract_reference(sms_text),
        "category": None,  # filled by categorizer
    }


# ─────────────────────────────────────────────────
# TRANSACTION CATEGORIZER
# ─────────────────────────────────────────────────

CATEGORIES = {
    "Food & Dining": {
        "keywords": ["zomato", "swiggy", "restaurant", "cafe", "pizza", "burger", "hotel",
                     "dhaba", "biryani", "food", "eat", "dining", "kitchen", "bakery",
                     "dominos", "mcdonald", "kfc", "subway", "starbucks", "chai"],
        "emoji": "🍽️",
        "color": "#FF6B6B",
    },
    "Groceries": {
        "keywords": ["bigbasket", "grofers", "blinkit", "zepto", "dmart", "more", "reliance fresh",
                     "supermarket", "grocery", "vegetables", "fruits", "kirana", "market"],
        "emoji": "🛒",
        "color": "#4ECDC4",
    },
    "Transport": {
        "keywords": ["uber", "ola", "rapido", "metro", "irctc", "railway", "bus", "taxi",
                     "auto", "petrol", "fuel", "pump", "parking", "toll", "namma metro",
                     "bmtc", "redbus", "makemytrip flight"],
        "emoji": "🚗",
        "color": "#45B7D1",
    },
    "Shopping": {
        "keywords": ["amazon", "flipkart", "myntra", "ajio", "nykaa", "meesho", "snapdeal",
                     "mall", "store", "shop", "clothing", "fashion", "lifestyle", "pantaloon",
                     "westside", "h&m", "zara"],
        "emoji": "🛍️",
        "color": "#96CEB4",
    },
    "Entertainment": {
        "keywords": ["netflix", "prime", "hotstar", "disney", "spotify", "youtube premium",
                     "bookmyshow", "pvr", "inox", "movie", "cinema", "game", "gaming",
                     "steam", "xbox", "playstation"],
        "emoji": "🎬",
        "color": "#FFEAA7",
    },
    "Utilities & Bills": {
        "keywords": ["electricity", "prepaid", "postpaid", "recharge", "broadband", "wifi",
                     "airtel", "jio", "bsnl", "vi vodafone", "water bill", "gas cylinder",
                     "lpg", "tata sky", "dish tv", "fastag"],
        "emoji": "💡",
        "color": "#DDA0DD",
    },
    "Health": {
        "keywords": ["pharmacy", "medical", "hospital", "clinic", "doctor", "medicine",
                     "pharmeasy", "1mg", "netmeds", "apollo", "manipal", "lab", "diagnostic",
                     "gym", "fitpass", "cult.fit"],
        "emoji": "🏥",
        "color": "#98FB98",
    },
    "Education": {
        "keywords": ["udemy", "coursera", "unacademy", "byju", "vedantu", "fees", "college",
                     "university", "school", "tuition", "coaching", "upgrad", "simplilearn"],
        "emoji": "📚",
        "color": "#F0E68C",
    },
    "Transfers": {
        "keywords": ["transfer", "sent", "neft", "imps", "rtgs", "upi", "paytm", "phonepe",
                     "gpay", "google pay", "bhim"],
        "emoji": "💸",
        "color": "#B0C4DE",
    },
    "Other": {
        "keywords": [],
        "emoji": "📌",
        "color": "#D3D3D3",
    },
}


def categorize_transaction(transaction):
    """Assign a spending category based on merchant and raw SMS text."""
    search_text = (transaction.get("merchant", "") + " " + transaction.get("raw", "")).lower()
    
    for category, data in CATEGORIES.items():
        if category == "Other":
            continue
        for kw in data["keywords"]:
            if kw in search_text:
                return category
    
    return "Other"


# ─────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "FinSight API",
        "version": "1.0.0",
        "gemini_configured": model is not None,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    })


@app.route("/api/parse", methods=["POST"])
def parse_sms_route():
    """
    Parse one or more SMS messages.
    Body: { "messages": ["sms1", "sms2", ...] }
    """
    data = request.get_json(force=True)
    messages = data.get("messages", [])
    
    if not messages:
        return jsonify({"error": "No messages provided"}), 400
    
    transactions = []
    skipped = 0
    
    for i, sms in enumerate(messages):
        if not isinstance(sms, str) or not sms.strip():
            skipped += 1
            continue
        
        tx = parse_sms(sms)
        if tx is None:
            skipped += 1
            continue
        
        tx["id"] = f"tx_{i+1:04d}"
        tx["category"] = categorize_transaction(tx)
        transactions.append(tx)
    
    # Build summary
    total_debit = sum(t["amount"] for t in transactions if t["type"] == "debit")
    total_credit = sum(t["amount"] for t in transactions if t["type"] == "credit")
    
    # Category breakdown
    category_totals = {}
    for tx in transactions:
        if tx["type"] == "debit":
            cat = tx["category"]
            category_totals[cat] = category_totals.get(cat, 0) + tx["amount"]
    
    category_breakdown = []
    for cat, total in sorted(category_totals.items(), key=lambda x: -x[1]):
        category_breakdown.append({
            "category": cat,
            "total": round(total, 2),
            "emoji": CATEGORIES.get(cat, CATEGORIES["Other"])["emoji"],
            "color": CATEGORIES.get(cat, CATEGORIES["Other"])["color"],
            "percentage": round((total / total_debit * 100) if total_debit > 0 else 0, 1),
        })
    
    return jsonify({
        "transactions": transactions,
        "summary": {
            "total_transactions": len(transactions),
            "skipped": skipped,
            "total_debit": round(total_debit, 2),
            "total_credit": round(total_credit, 2),
            "net": round(total_credit - total_debit, 2),
            "category_breakdown": category_breakdown,
            "categories_meta": {k: {"emoji": v["emoji"], "color": v["color"]} for k, v in CATEGORIES.items()},
        },
    })


@app.route("/api/chat", methods=["POST"])
def pocket_coach():
    """
    PocketCoach AI endpoint.
    Body: {
        "message": "user question",
        "transactions": [...],   // parsed transactions for context
        "history": [...]         // previous chat turns
    }
    """
    if not model:
        return jsonify({"error": "Gemini API key not configured. Set GEMINI_API_KEY in .env"}), 503
    
    data = request.get_json(force=True)
    user_message = data.get("message", "").strip()
    transactions = data.get("transactions", [])
    history = data.get("history", [])
    
    if not user_message:
        return jsonify({"error": "Message is required"}), 400
    
    # Build financial context from transactions
    financial_context = ""
    if transactions:
        total_debit = sum(t["amount"] for t in transactions if t["type"] == "debit")
        total_credit = sum(t["amount"] for t in transactions if t["type"] == "credit")
        
        category_totals = {}
        for tx in transactions:
            if tx["type"] == "debit":
                cat = tx["category"]
                category_totals[cat] = category_totals.get(cat, 0) + tx["amount"]
        
        top_categories = sorted(category_totals.items(), key=lambda x: -x[1])[:5]
        category_str = "\n".join(
            f"  - {cat}: ₹{total:,.0f} ({total/total_debit*100:.1f}%)" 
            for cat, total in top_categories
        ) if total_debit > 0 else "  No debit data available"
        
        top_merchants = {}
        for tx in transactions:
            if tx["type"] == "debit" and tx["merchant"] != "Unknown Merchant":
                top_merchants[tx["merchant"]] = top_merchants.get(tx["merchant"], 0) + tx["amount"]
        top_m = sorted(top_merchants.items(), key=lambda x: -x[1])[:5]
        merchant_str = "\n".join(f"  - {m}: ₹{a:,.0f}" for m, a in top_m) if top_m else "  No merchant data"
        
        financial_context = f"""
=== USER'S FINANCIAL SNAPSHOT ===
Total Spent:    ₹{total_debit:,.2f}
Total Received: ₹{total_credit:,.2f}
Net Flow:       ₹{total_credit - total_debit:+,.2f}
Transactions:   {len(transactions)}

Top Spending Categories:
{category_str}

Top Merchants:
{merchant_str}
=================================
"""
    
    # Build system prompt
    system_prompt = f"""You are PocketCoach — a friendly, sharp, and empathetic personal finance AI coach for Indian users. 
You specialize in personal finance advice grounded in the user's actual spending data from their bank SMS messages.

Guidelines:
- Be conversational, warm, and encouraging — not preachy
- Use Indian context: ₹ symbol, Indian financial terms, Indian banks (SBI, HDFC, ICICI, etc.)
- Give specific, actionable advice based on THEIR actual numbers
- Point out patterns, suggest realistic cuts, celebrate wins
- Keep responses concise but insightful (3-5 bullet points or short paragraphs max)
- If asked about data you don't have, be honest and helpful about what you CAN see
- Use emojis sparingly but effectively
- Reference actual figures from their spending when relevant

{financial_context if financial_context else "Note: No transaction data loaded yet. Give general advice and encourage the user to paste their SMS messages."}
"""
    
    # Build conversation for Gemini
    try:
        # Format history for Gemini multi-turn
        contents = []
        for turn in history[-10:]:  # last 10 turns for context
            role = turn.get("role", "user")
            text = turn.get("content", "")
            if role == "user":
                contents.append({"role": "user", "parts": [text]})
            else:
                contents.append({"role": "model", "parts": [text]})
        
        # Add current message
        contents.append({"role": "user", "parts": [user_message]})
        
        response = model.generate_content(
            contents,
            generation_config={
                "temperature": 0.7,
                "max_output_tokens": 1024,
            },
            system_instruction=system_prompt,
        )
        
        reply = response.text.strip()
        
        return jsonify({
            "reply": reply,
            "tokens_used": response.usage_metadata.total_token_count if hasattr(response, "usage_metadata") else None,
        })
    
    except Exception as e:
        return jsonify({"error": f"Gemini API error: {str(e)}"}), 500


@app.route("/api/categories", methods=["GET"])
def get_categories():
    """Return category metadata for frontend."""
    return jsonify({
        "categories": {
            k: {"emoji": v["emoji"], "color": v["color"]}
            for k, v in CATEGORIES.items()
        }
    })


@app.route("/api/sample", methods=["GET"])
def get_sample():
    """Return sample SMS messages for demo/testing."""
    samples = [
        "Your A/c XX4521 debited INR 450.00 on 12-Apr-24 at Zomato. Avl Bal: INR 12,340.50. Ref No 123456789",
        "Rs.1,200 debited from your HDFC Bank A/c ending 7823 for Flipkart order on 11-Apr-24. Available balance: Rs.11,140.50",
        "INR 85.00 debited from A/c XX4521 at Ola Cabs on 11-Apr-24. UPI Ref: 405678901234",
        "Dear Customer, INR 3,500 credited to your A/c XX4521 on 10-Apr-24. Ref: SAL202404",
        "Your A/c XX4521 debited INR 299.00 on 10-Apr-24 at Netflix. Avl Bal: INR 14,641.50",
        "Rs.650 debited from A/c XX4521 at Apollo Pharmacy on 09-Apr-24. Balance: Rs.14,992.50",
        "INR 2,100 debited from your SBI A/c ending 4521 via UPI to Airtel Prepaid on 09-Apr-24",
        "Your A/c XX4521 debited INR 750.00 at BigBasket on 08-Apr-24. Avl Bal: INR 17,092.50",
        "Rs.180.00 debited from A/c XX4521 at Rapido Bike on 07-Apr-24. UPI Ref: 305678123456",
        "INR 55,000 credited to your HDFC Salary A/c XX4521 on 01-Apr-24. Avl Bal: INR 67,850.00",
        "Your A/c XX4521 debited INR 1,800 at Myntra on 06-Apr-24. Avl Bal: INR 65,750.00",
        "Rs.400 debited from A/c XX4521 at Swiggy Instamart on 05-Apr-24. Bal: Rs.65,350.00",
        "INR 500.00 debited from your A/c XX4521 at PVR Cinemas on 04-Apr-24. UPI Ref: 205600012345",
        "Your A/c XX4521 debited INR 1,200 at DMart on 03-Apr-24. Available Bal: INR 64,150.00",
        "Rs.3,000 debited from A/c XX4521 transferred to Savings via IMPS on 02-Apr-24",
    ]
    return jsonify({"samples": samples, "count": len(samples)})


# ─────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    print(f"[FinSight] API running on http://localhost:{port}")
    print(f"[FinSight] Gemini configured: {model is not None}")
    app.run(host="0.0.0.0", port=port, debug=debug)
