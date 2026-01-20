from flask import Blueprint, send_file, session
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

download_bp = Blueprint("download", __name__)

@download_bp.route("/download_score_pdf")
def download_score_pdf():
    pdf_path = "technical_score.pdf"

    pdfmetrics.registerFont(UnicodeCIDFont("HYSMyeongJo-Medium"))

    doc = SimpleDocTemplate(pdf_path)
    styles = getSampleStyleSheet()
    story = []

    score = session.get("last_score", 0)
    total = session.get("total_questions", 100)
    company = session.get("last_company", "Unknown")
    round_name = session.get("last_round", "Technical")

    story.append(Paragraph(f"{company} – {round_name} Results", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Final Score: {score} / {total}", styles["Heading2"]))
    story.append(Spacer(1, 12))

    feedback = session.get("technical_feedback", {})

    if feedback:
        story.append(Paragraph("Improvement Areas:", styles["Heading3"]))
        for q, data in feedback.items():
            story.append(Paragraph(f"Question: {q}", styles["BodyText"]))
            story.append(Paragraph(
                f"Missing Key Terms: {', '.join(data.get('missing_key_terms', []))}",
                styles["BodyText"]
            ))
            story.append(Paragraph(
                f"Missing Key Points: {', '.join(data.get('missing_key_points', []))}",
                styles["BodyText"]
            ))
            story.append(Spacer(1, 8))
    else:
        story.append(Paragraph("No weak topics detected.", styles["BodyText"]))

    doc.build(story)

    return send_file(pdf_path, as_attachment=True)
