import base64
import hashlib
import json
from html import escape
import streamlit as st
import streamlit.components.v1 as components
from reports import grouped, report_text, report_pdf, publication_time

PENDING_COLOR = '#EAA1CF'
GOLD = '#EACA7A'
SUBJECT_COLORS = ['#EACA7A', '#95CFC3', '#ABA9F3', '#EBAF8F', '#A8CE8B', '#92BEE8']
CSS = '''
<style>
.stApp {background:#141213;color:#F6F4F1}
.block-container {max-width:960px;padding:2rem 1.2rem 5rem}
[data-testid="stHeader"] {background:transparent}
input, [data-baseweb="select"]>div {border-radius:32px!important;background:#272526!important;color:#F6F4F1!important}
input {padding:1.3rem!important}
[data-testid="stForm"] {border:0;padding:0;margin-bottom:1rem}
[data-testid="stForm"] [data-testid="stHorizontalBlock"] {display:flex!important;flex-wrap:nowrap!important;align-items:center;gap:8px!important;background:#343236;border:1px solid #555158;border-radius:999px;padding:8px 10px 8px 20px;transition:border-color .2s,box-shadow .2s}
[data-testid="stForm"] [data-testid="stHorizontalBlock"]:focus-within {border-color:#EACA7A;box-shadow:0 0 0 2px #EACA7A22}
[data-testid="stForm"] :is([data-testid="column"],[data-testid="stColumn"]):first-child {flex:1 1 0!important;width:0!important;min-width:0!important}
[data-testid="stForm"] :is([data-testid="column"],[data-testid="stColumn"]):last-child {flex:0 0 100px!important;width:100px!important;min-width:0!important}
[data-testid="stForm"] [data-testid="stTextInput"] [data-baseweb="input"] {background:transparent!important;border:0!important;box-shadow:none!important;border-radius:0!important}
[data-testid="stForm"] input {height:48px!important;padding:0!important;background:transparent!important;border-radius:0!important;font-size:1.1rem!important}
[data-testid="stForm"] input::placeholder {color:#C3BEC6!important;opacity:1}
[data-testid="stFormSubmitButton"] button {width:100%;min-height:48px;background:#EACA7A!important;color:#211B10!important;border:1px solid #EACA7A!important;font-weight:650}
[data-testid="stFormSubmitButton"] button:hover {background:#F3D993!important;border-color:#F3D993!important}
[data-testid="stFormSubmitButton"] button:focus-visible {outline:2px solid #F6F4F1;outline-offset:3px}
button {border-radius:28px!important}
.stApp h1.search-title {font-size:clamp(2rem,6vw,4.4rem)!important;font-weight:550;line-height:1.12;letter-spacing:-.055em;color:#F6F4F1;margin:12px 0 0;padding:0}
.brand {display:flex;justify-content:space-between;gap:12px;align-items:start}
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
    text = report_text(student, records, updated_at)
    # JSON escapes prevent a student name or code from breaking out of script context.
    payload = json.dumps(text).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    pdf = base64.b64encode(report_pdf(student, records, updated_at)).decode()
    title = escape(student['Student Name'] + ' · ' + student['Group'])
    components.html('''<style>
*{box-sizing:border-box}body{margin:0;background:#141213;color:#F6F4F1;font:16px system-ui}
#results{height:640px;overflow:auto;padding:0 10px 100px;scroll-behavior:smooth}
h2{font-size:24px;margin:0;min-width:0;overflow-wrap:anywhere}.student-heading{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:14px 20px;margin:16px 0 32px}.student-heading h2{flex:1 1 220px}.student-totals{display:flex;flex-wrap:wrap;justify-content:flex-end;gap:8px;margin-left:auto}.student-total{display:inline-flex;align-items:center;gap:10px;border-radius:999px;padding:5px 8px 5px 14px;font-size:15px;font-weight:650;white-space:nowrap}.student-total-number{display:inline-flex;align-items:center;justify-content:center;min-width:28px;height:28px;border-radius:999px;padding:0 6px;color:#141213;font-size:14px;font-weight:750;font-variant-numeric:tabular-nums}@media(max-width:480px){.student-heading{gap:12px}.student-heading h2{flex-basis:100%}.student-total{font-size:14px}}details{margin:24px 0}summary{padding-left:12px;font-size:22px;font-weight:650;cursor:pointer;list-style:none;display:flex;align-items:center;gap:10px}summary:after{content:'⌄';padding:0 12px;flex-shrink:0}details:not([open]) summary:after{content:'›'}
.subject-name{min-width:0;overflow-wrap:anywhere}.subject-counts{margin-left:auto;display:flex;gap:7px;flex-shrink:0}.status-count{width:34px;height:34px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;color:#141213;font-size:14px;font-weight:750;font-variant-numeric:tabular-nums}
.badge{display:inline-block;margin:22px 0 8px;padding:3px 14px;border-radius:22px;font-weight:600}ol{padding-left:25px;margin:0}li{padding:8px 0;overflow-wrap:anywhere;line-height:1.7}li span{color:#BDB8BC}
button,a{font:inherit;color:#F6F4F1;background:#302C2D;border:1px solid #696064;padding:10px 15px;border-radius:24px;cursor:pointer;text-decoration:none}
button:focus-visible,a:focus-visible,summary:focus-visible{outline:2px solid #EACA7A;outline-offset:3px}
#plus,#top{position:fixed;bottom:16px;z-index:10;background:#302A20;color:#EACA7A;box-shadow:0 3px 16px #0008}#plus{right:18px;width:48px;height:48px;font-size:25px;padding:0}#top{right:76px;width:48px;height:48px;padding:0;display:flex;align-items:center;justify-content:center}
#menu{position:fixed;bottom:75px;right:18px;background:#242122;padding:14px;border:1px solid #635B51;border-radius:18px;max-width:290px}#menu button,#menu a{display:block;margin:8px 0;width:100%;text-align:center}#feedback{font-size:13px;color:#EACA7A}
</style>''' + f'<main id="results"><div class="student-heading"><h2>{title}</h2><div class="student-totals" role="group" aria-label="Totals across all subjects">{"".join(total_badges)}</div></div>{"".join(sections) if records else "<p>No matching quizzes for these filters.</p>"}</main><button id="top" aria-label="Back to search" title="Back to search"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 20V4M5 11l7-7 7 7"/></svg></button><button id="plus" aria-label="Report actions" aria-expanded="false" aria-controls="menu">+</button><div id="menu" hidden><button id="share">Share report</button><button id="copy">Copy report</button><a download="quiz-report.pdf" href="data:application/pdf;base64,{pdf}">Download PDF</a><p id="feedback" role="status"></p></div>' + '''<script>
const text=PAYLOAD;
const results=document.getElementById('results'), topButton=document.getElementById('top'), plus=document.getElementById('plus'), menu=document.getElementById('menu'), feedback=document.getElementById('feedback');

topButton.onclick=()=>{results.scrollTo({top:0,behavior:'smooth'}); try{const doc=window.parent.document;const input=doc.querySelector('input[aria-label=\"Student Number\"],input[aria-label=\"Name or Student Number\"]');if(input){input.scrollIntoView({behavior:'smooth',block:'center'});input.focus({preventScroll:true});}}catch(e){}};
plus.onclick=()=>{menu.hidden=!menu.hidden;plus.setAttribute('aria-expanded',String(!menu.hidden));};
async function copy(){try{await navigator.clipboard.writeText(text);feedback.textContent='Report copied.';}catch(e){const area=document.createElement('textarea');area.value=text;menu.append(area);area.select();feedback.textContent=document.execCommand('copy')?'Report copied.':'Select and copy the report below.';}}
document.getElementById('copy').onclick=copy;
document.getElementById('share').onclick=async()=>{if(navigator.share){try{await navigator.share({title:'SABIS Quiz Status',text});}catch(e){if(e.name!=='AbortError')await copy();}}else await copy();};
document.addEventListener('keydown',e=>{if(e.key==='Escape'){menu.hidden=true;plus.setAttribute('aria-expanded','false');plus.focus();}});
</script>'''.replace('PAYLOAD', payload), height=650, scrolling=False)
