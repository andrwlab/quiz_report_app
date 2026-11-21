import base64
import hashlib
from html import escape
import streamlit as st
from reports import grouped, report_text, report_pdf, publication_time

PENDING_COLOR = '#ED6D83'
COMPLETE_COLOR = '#BEF0D5'
GOLD = '#EACA7A'
SUBJECT_COLORS = ['#EACA7A', '#95CFC3', '#ABA9F3', '#EBAF8F', '#A8CE8B', '#92BEE8']
CSS = '''
<style>
html,body,#root,[data-testid="stApp"],[data-testid="stAppViewContainer"],[data-testid="stMain"] {background:#141213!important;color:#F6F4F1;color-scheme:dark!important}
.stApp {background:#141213;color:#F6F4F1}
[data-testid="stMainBlockContainer"],.block-container {padding-top:calc(var(--quiz-host-top,72px) + 24px + env(safe-area-inset-top,0px))!important;padding-bottom:calc(var(--quiz-host-bottom,72px) + 94px + env(safe-area-inset-bottom,0px))!important}
[data-testid="stMain"] {scroll-padding-top:calc(var(--quiz-host-top,72px) + 20px)}
.block-container {max-width:960px;padding:2rem 1.2rem 5rem}
[data-testid="stHeader"] {background:#141213!important}
input, [data-baseweb="select"]>div {border-radius:32px!important;background:#272526!important;color:#F6F4F1!important}
input {padding:1.3rem!important}
[data-testid="stForm"] {border:0;padding:0;margin-bottom:1rem}
[data-testid="stForm"] [data-testid="stHorizontalBlock"] {display:flex!important;flex-wrap:nowrap!important;align-items:center;gap:8px!important;background:#343236;border:1px solid #555158;border-radius:999px;padding:8px 10px 8px 20px;transition:border-color .2s,box-shadow .2s}
[data-testid="stForm"] [data-testid="stHorizontalBlock"]:focus-within {border-color:#EACA7A;box-shadow:0 0 0 2px #EACA7A22}
[data-testid="stForm"] :is([data-testid="column"],[data-testid="stColumn"]):first-child {flex:1 1 0!important;width:0!important;min-width:0!important}
[data-testid="stForm"] :is([data-testid="column"],[data-testid="stColumn"]):last-child {flex:0 0 100px!important;width:100px!important;min-width:0!important}
[data-testid="stForm"] [data-testid="stTextInput"] [data-baseweb="input"] {background:transparent!important;border:0!important;box-shadow:none!important;border-radius:0!important}
[data-testid="stForm"] [data-testid="stTextInputRootElement"],[data-testid="stForm"] [data-testid="stTextInputRootElement"] > div,[data-testid="stForm"] [data-testid="stTextInput"],[data-testid="stForm"] [data-baseweb="input"],[data-testid="stForm"] [data-baseweb="input"] > div {background:transparent!important;background-color:transparent!important;border:0!important;box-shadow:none!important}
[data-testid="stForm"] input {appearance:none!important;-webkit-appearance:none!important;-webkit-text-fill-color:#F6F4F1!important;box-shadow:none!important;border:0!important;outline:none!important;height:48px!important;padding:0!important;background:transparent!important;border-radius:0!important;font-size:1.1rem!important}
[data-testid="stForm"] input::placeholder {color:#C3BEC6!important;opacity:1}
[data-testid="stFormSubmitButton"] button {width:100%;min-height:48px;background:#EACA7A!important;color:#211B10!important;border:1px solid #EACA7A!important;font-weight:650}
[data-testid="stFormSubmitButton"] button:hover {background:#F3D993!important;border-color:#F3D993!important}
[data-testid="stFormSubmitButton"] button:focus-visible {outline:2px solid #F6F4F1;outline-offset:3px}
[data-testid="stForm"] input:-webkit-autofill {-webkit-box-shadow:0 0 0 1000px #343236 inset!important;-webkit-text-fill-color:#F6F4F1!important}
button {border-radius:28px!important}
.stApp h1.search-title {font-size:clamp(2rem,6vw,4.4rem)!important;font-weight:550;line-height:1.12;letter-spacing:-.055em;color:#F6F4F1;margin:12px 0 0;padding:0}
.brand {display:flex;flex-wrap:wrap;justify-content:space-between;gap:12px;align-items:start}
.power {margin-left:auto}
.power {color:#EACA7A;font-style:italic;font-size:.85rem;text-align:right}
.meta {color:#BBB7B9;font-size:.85rem;margin:8px 0 20px}
.book {text-align:center;color:#EACA7A;margin:42px 0 32px}
@media(max-width:480px){.book{margin:30px 0 26px}[data-testid="stForm"] [data-testid="stHorizontalBlock"]{padding:6px 7px 6px 15px}[data-testid="stForm"] :is([data-testid="column"],[data-testid="stColumn"]):last-child{flex-basis:80px!important;width:80px!important}[data-testid="stForm"] input{font-size:1rem!important}}
</style>'''


def header(snapshot):
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown('<div class="brand"><strong>SABIS Quiz Status</strong><span class="power">Powered by The Mister</span></div>', unsafe_allow_html=True)
    updated = publication_time(snapshot['updated_at']) + ' · America/Panama' if snapshot else 'Not published yet'
    st.markdown(f'<div class="meta">Data last updated&nbsp; | &nbsp;{escape(updated)}</div>', unsafe_allow_html=True)
    st.markdown('''<div class="book"><svg width="54" height="44" viewBox="0 0 80 64" fill="none" stroke="currentColor" stroke-width="4" aria-label="Open book" role="img"><path d="M40 13Q22 0 4 12V57Q22 46 40 59Q58 46 76 57V12Q58 0 40 13V59"/></svg><h1 class="search-title">SABIS Quiz Status</h1></div>''', unsafe_allow_html=True)


def render_student(student, records, updated_at, *, all_records=None):
    total_records = records if all_records is None else all_records
    all_current = not any(record['status'] in ('Pending', 'Low Score') for record in total_records)
    total_badges = []
    for status, tone in [('Pending', PENDING_COLOR), ('Low Score', GOLD)]:
        total = sum(record['status'] == status for record in total_records)
        total_badges.append(
            f'<span class="student-total" style="color:{tone};background:{tone}20" '
            f'aria-label="{total} {status} quizzes across all subjects">'
            f'<span>{status}</span><span class="student-total-number" style="background:{tone}">{total}</span></span>'
        )
    sections = []
    for subject, statuses in grouped(records).items():
        color = SUBJECT_COLORS[int(hashlib.sha256(subject.encode()).hexdigest(), 16) % len(SUBJECT_COLORS)]
        body = []
        counts = []
        for status in ('Pending', 'Low Score'):
            if status not in statuses:
                continue
            tone = PENDING_COLOR if status == 'Pending' else GOLD
            count = len(statuses[status])
            if count:
                counts.append(
                    f'<span class="status-count" style="background:{tone}" '
                    f'aria-label="{count} {status} quizzes" title="{status}: {count}">{count}</span>'
                )
            body.append(f'<span class="badge" style="color:{tone};background:{tone}20">{status}</span><ol>')
            for record in statuses[status]:
                body.append(f'<li><strong>{escape(record["code"])}</strong> <span>— {escape(record["week"])}</span></li>')
            body.append('</ol>')
        sections.append(f'<details open><summary style="border-left:4px solid {color}"><span class="subject-name">{escape(subject)}</span><span class="subject-counts">{"".join(counts)}</span></summary>{"".join(body)}</details>')
    completion = (
        '<div class="quiz-all-current" role="status">'
        '<svg class="completion-icon" viewBox="0 0 100 100" role="img" aria-label="Student up to date">'
        f'<circle class="completion-disc" cx="50" cy="50" r="45" fill="{COMPLETE_COLOR}"/>'
        '<path class="completion-check" d="M29 51l14 14 29-30" fill="none" stroke="#FFFFFF" '
        'stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>'
        '</svg><p class="completion-title">This student is up to date</p></div>'
    )
    title = escape(student['Student Name'] + ' · ' + student['Group'])
    st.html(
        '<style>' + RESULT_STYLES + '</style>'
        + f'<section class="quiz-results"><div class="student-heading"><h2>{title}</h2>'
        + (f'<div class="student-totals" role="group" aria-label="Totals across all subjects">{"".join(total_badges)}</div>' if not all_current else '')
        + '</div>'
        + (completion if all_current else ''.join(sections) if records else '<p>No matching quizzes for these filters.</p>')
        + '</section>'
    )
    return {
        'title': student['Student Name'] + ' · ' + student['Group'],
        'text': report_text(student, records, updated_at),
        'pdf': base64.b64encode(report_pdf(student, records, updated_at)).decode(),
    }


RESULT_STYLES = """
.quiz-results{color:#F6F4F1;font:16px system-ui;padding:0 4px 24px}
.quiz-results *{box-sizing:border-box}
.quiz-results h2{font-size:24px;line-height:1.3;margin:0;min-width:0;overflow-wrap:anywhere}
.quiz-results .student-heading{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:14px 20px;margin:16px 0 32px}
.quiz-results .student-heading h2{flex:1 1 220px}
.quiz-results .student-totals{display:flex;flex-wrap:wrap;justify-content:flex-end;gap:8px;margin-left:auto}
.quiz-results .student-total{display:inline-flex;align-items:center;gap:10px;border-radius:999px;padding:5px 8px 5px 14px;font-size:15px;font-weight:650;white-space:nowrap}
.quiz-results .student-total-number{display:inline-flex;align-items:center;justify-content:center;min-width:28px;height:28px;border-radius:999px;padding:0 6px;color:#141213;font-size:14px;font-weight:750;font-variant-numeric:tabular-nums}
.quiz-results .quiz-all-current{min-height:250px;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:28px 16px}
.quiz-results .completion-icon{width:108px;height:108px;overflow:visible}
.quiz-results .completion-disc{transform-origin:50px 50px;animation:sabis-complete-circle .45s ease-out both}
.quiz-results .completion-check{stroke-dasharray:66;stroke-dashoffset:66;filter:drop-shadow(0 1px 1px #28584035);animation:sabis-complete-check .5s .25s ease-out both}
.quiz-results .completion-title{font-size:22px;font-weight:650;margin:22px 0 6px}
.quiz-results .completion-caption{font-size:15px;color:#BDB8BC;margin:0}
@keyframes sabis-complete-circle{from{opacity:0;transform:scale(.75)}to{opacity:1;transform:scale(1)}}
@keyframes sabis-complete-check{to{stroke-dashoffset:0}}
@media(prefers-reduced-motion:reduce){.quiz-results .completion-disc,.quiz-results .completion-check{animation:none;stroke-dashoffset:0}}
.quiz-results details{margin:24px 0}
.quiz-results summary{padding-left:12px;font-size:22px;font-weight:650;cursor:pointer;list-style:none;display:flex;align-items:center;gap:10px}
.quiz-results summary::-webkit-details-marker{display:none}
.quiz-results summary:after{content:'⌄';padding:0 12px;flex-shrink:0}
.quiz-results details:not([open]) summary:after{content:'›'}
.quiz-results summary:focus-visible{outline:2px solid #EACA7A;outline-offset:4px}
.quiz-results .subject-name{min-width:0;overflow-wrap:anywhere}
.quiz-results .subject-counts{margin-left:auto;display:flex;gap:7px;flex-shrink:0}
.quiz-results .status-count{width:34px;height:34px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;color:#141213;font-size:14px;font-weight:750;font-variant-numeric:tabular-nums}
.quiz-results .badge{display:inline-block;margin:22px 0 8px;padding:3px 14px;border-radius:22px;font-weight:600}
.quiz-results ol{padding-left:25px;margin:0}
.quiz-results li{padding:8px 0;overflow-wrap:anywhere;line-height:1.7}
.quiz-results li span{color:#BDB8BC}
@media(max-width:480px){.quiz-results .student-heading{gap:12px}.quiz-results .student-heading h2{flex-basis:100%}.quiz-results .student-total{font-size:14px}}
"""
