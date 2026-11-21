"""Individual reports are text and vector PDF, never screenshots."""
from collections import defaultdict
from datetime import datetime
from html import escape
from io import BytesIO
from zoneinfo import ZoneInfo


def publication_time(value):
    return datetime.fromisoformat(value).astimezone(ZoneInfo('America/Panama')).strftime('%b %d, %Y · %I:%M %p')


def grouped(records):
    result = defaultdict(lambda: defaultdict(list))
    for record in records:
        result[record['subject']][record['status']].append(record)
    return {subject: {status: sorted(items, key=lambda r: (r['week'], r['code'])) for status, items in statuses.items()} for subject, statuses in sorted(result.items())}


def report_text(student, records, updated_at):
    lines = [f"{student['Student Name']} · {student['Group']}", 'Data last updated: ' + publication_time(updated_at) + ' (America/Panama)']
    for subject, statuses in grouped(records).items():
        lines += ['', subject]
        for status in ('Pending', 'Low Score'):
            if status in statuses:
                lines.append(status)
                lines.extend(f"{i}. {r['code']} — {r['week']}" for i, r in enumerate(statuses[status], 1))
    if not records:
        lines.append('No matching quizzes.')
    return '\n'.join(lines)


def report_pdf(student, records, updated_at):
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    output = BytesIO()
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Mobile', fontName='Helvetica', fontSize=12, leading=18, spaceAfter=8, wordWrap='CJK'))
    story = []
    for index, line in enumerate(report_text(student, records, updated_at).splitlines()):
        if line:
            story.append(Paragraph(escape(line.replace('—', '-')), styles['Heading2'] if index == 0 else styles['Mobile']))
        else:
            story.append(Spacer(1, 10))
    SimpleDocTemplate(output, pagesize=(360, 640), rightMargin=24, leftMargin=24, topMargin=24, bottomMargin=28).build(story)
    return output.getvalue()
