from flask import Flask, request, jsonify
from flask_cors import CORS
import traceback

from utils.parser import extract_text_from_pdf
from utils.skills import get_skill_match
from utils.nlp_analyzer import analyze_with_nlp
from utils.bert_analyzer import get_bert_similarity
from utils.gemini_ai import get_ai_insights

app = Flask(__name__)
CORS(app)  # single CORS — no manual after_request headers


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "Flask is running"})


@app.route("/analyze", methods=["POST", "OPTIONS"])
def analyze():
    if request.method == "OPTIONS":
        return "", 204

    try:
        print("\n========== NEW REQUEST ==========")

        if "resume" not in request.files:
            return jsonify({"error": "No resume file uploaded"}), 400

        file = request.files["resume"]
        job_desc = request.form.get("job_desc", "").strip()

        if not job_desc:
            return jsonify({"error": "Job description is empty"}), 400

        # Step 1 — Extract PDF text
        print("[1/5] Extracting PDF text...")
        resume_text = extract_text_from_pdf(file.stream)
        if not resume_text:
            return jsonify({"error": "Could not extract text from PDF. Make sure it is not a scanned image."}), 400
        print(f"      {len(resume_text)} characters extracted")

        # Step 2 — Skill matching
        print("[2/5] Skill matching...")
        matched_skills, missing_skills, skill_score = get_skill_match(resume_text, job_desc)

        # Step 3 — spaCy NLP
        print("[3/5] spaCy NLP analysis...")
        nlp_result = analyze_with_nlp(resume_text, job_desc)

        # Step 4 — BERT semantic similarity
        print("[4/5] BERT similarity...")
        bert_score = get_bert_similarity(resume_text, job_desc)

        # Step 5 — Gemini AI insights
        print("[5/5] Gemini AI insights...")
        ai_insights = get_ai_insights(resume_text, job_desc)

        # Weighted ATS score
        final_score = round(
            (0.40 * bert_score) +
            (0.35 * skill_score) +
            (0.25 * nlp_result["keyword_overlap_score"]),
            1
        )

        print(f"      Score: {final_score} | BERT:{bert_score} SKILL:{skill_score} KW:{nlp_result['keyword_overlap_score']}")
        print("=================================\n")

        return jsonify({
            "score":           final_score,
            "bert_score":      round(bert_score, 1),
            "skill_score":     round(skill_score, 1),
            "keyword_score":   round(nlp_result["keyword_overlap_score"], 1),
            "matched_skills":  matched_skills,
            "missing_skills":  missing_skills,
            "resume_keywords": nlp_result["resume_keywords"],
            "job_keywords":    nlp_result["job_keywords"],
            "entities":        nlp_result["entities"],
            "education":       nlp_result.get("education", []),
            "experience":      nlp_result.get("experience", []),
            "insights":        ai_insights,
        })

    except Exception as e:
        print("ERROR:", e)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("🚀  Resume Analyzer running → http://127.0.0.1:5001")
    app.run(debug=True, port=5001)
