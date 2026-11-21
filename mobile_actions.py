"""Viewport actions without an iframe, with safe-area spacing for mobile browsers."""
from streamlit.components.v2 import component

HTML = '''
<div class="quiz-mobile-shell">
  <nav class="quiz-fab-bar" aria-label="Report actions">
    <button type="button" class="quiz-fab" data-top aria-label="Back to search" title="Back to search"><svg width="23" height="23" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 20V4M5 11l7-7 7 7"/></svg></button>
    <button type="button" class="quiz-fab" data-plus aria-label="Report actions" aria-expanded="false" aria-controls="quiz-report-menu"><svg width="23" height="23" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><path d="M12 4v16M4 12h16"/></svg></button>
  </nav>
  <section id="quiz-report-menu" class="quiz-fab-menu" data-menu hidden aria-label="Share or download report">
    <p data-empty>Search for a student to share or download a report.</p>
    <label data-picker hidden>Student<select data-select aria-label="Student report"></select></label>
    <button type="button" data-share>Share report</button>
    <button type="button" data-copy>Copy report</button>
    <a data-pdf download="quiz-report.pdf">Download PDF</a>
    <p data-feedback role="status"></p>
  </section>
</div>
'''

CSS = '''
html,body,#root,[data-testid="stApp"],[data-testid="stAppViewContainer"],[data-testid="stMain"]{background-color:#141213!important;color-scheme:dark!important}
.quiz-mobile-shell{font:16px system-ui;color:#F6F4F1}
.quiz-mobile-shell *{box-sizing:border-box}
.quiz-fab-bar{position:fixed;right:calc(18px + env(safe-area-inset-right,0px));bottom:calc(var(--quiz-host-bottom,72px) + 20px + env(safe-area-inset-bottom,0px));display:flex;gap:10px;z-index:2147483646}
.quiz-mobile-shell .quiz-fab{appearance:none;-webkit-appearance:none;display:inline-flex;align-items:center;justify-content:center;width:50px;height:50px;border-radius:50%!important;padding:0;color:#EACA7A!important;background:#302A20!important;border:1px solid #817869;box-shadow:0 3px 16px #0008;cursor:pointer;touch-action:manipulation}
.quiz-mobile-shell button:focus-visible,.quiz-mobile-shell a:focus-visible,.quiz-mobile-shell select:focus-visible{outline:2px solid #EACA7A;outline-offset:4px}
.quiz-fab-menu{position:fixed;right:calc(18px + env(safe-area-inset-right,0px));bottom:calc(var(--quiz-host-bottom,72px) + 82px + env(safe-area-inset-bottom,0px));z-index:2147483646;background:#242122;border:1px solid #635B51;border-radius:18px;padding:14px;width:min(300px,calc(100vw - 36px));max-height:calc(100dvh - var(--quiz-host-top,72px) - var(--quiz-host-bottom,72px) - 150px);overflow:auto;color:#F6F4F1;box-shadow:0 5px 24px #0008}
.quiz-mobile-shell [hidden]{display:none!important}
.quiz-fab-menu button,.quiz-fab-menu a,.quiz-fab-menu select{font:inherit;display:block;width:100%;margin:8px 0;padding:10px 12px;text-align:center;border-radius:22px!important;border:1px solid #696064;background:#302C2D;color:#F6F4F1;text-decoration:none;cursor:pointer}
.quiz-fab-menu p{font-size:14px;line-height:1.5;margin:8px 0}
.quiz-fab-menu [data-feedback]{color:#EACA7A}
.quiz-fab-menu textarea{width:100%;height:150px;background:#141213;color:#F6F4F1;font:14px system-ui}
'''

JS = r'''
export default function({data, parentElement}) {
  const template = parentElement.querySelector('.quiz-mobile-shell');
  const root = template.cloneNode(true);
  template.hidden = true;
  root.hidden = false;
  document.body.append(root);
  const top = root.querySelector('[data-top]');
  const plus = root.querySelector('[data-plus]');
  const menu = root.querySelector('[data-menu]');
  menu.id = 'quiz-active-report-menu';
  plus.setAttribute('aria-controls', menu.id);
  const share = root.querySelector('[data-share]');
  const copyButton = root.querySelector('[data-copy]');
  const pdf = root.querySelector('[data-pdf]');
  const feedback = root.querySelector('[data-feedback]');
  const select = root.querySelector('[data-select]');
  const reports = data?.reports || [];
  let selected = 0;

  function theme(doc) {
    doc.documentElement.style.backgroundColor = '#141213';
    doc.documentElement.style.colorScheme = 'dark';
    doc.body.style.backgroundColor = '#141213';
    for (const [name, content] of [['theme-color','#141213'],['color-scheme','dark'],['apple-mobile-web-app-status-bar-style','black']]) {
      let metas = Array.from(doc.head.querySelectorAll(`meta[name="${name}"]`));
      if (!metas.length) { const meta=doc.createElement('meta'); meta.name=name; doc.head.append(meta); metas=[meta]; }
      metas.forEach(meta=>{meta.content=content;meta.removeAttribute('media');});
    }
    const viewport = doc.head.querySelector('meta[name="viewport"]');
    if (viewport && !viewport.content.includes('viewport-fit')) viewport.content += ', viewport-fit=cover';
  }
  theme(document);
  try { if (window.top !== window) theme(window.top.document); } catch (_) {}

  // Reserve space for Streamlit controls, including cross-origin hosting chrome.
  let layoutFrame = 0;
  function updateInsets() {
    layoutFrame = 0;
    const height = window.innerHeight;
    let topInset = 72, bottomInset = 72;
    for (const el of document.querySelectorAll('[data-testid="stHeader"],[data-testid="stToolbar"]')) {
      const rect = el.getBoundingClientRect();
      if (rect.width && rect.height && rect.top >= 0 && rect.top < 100 && rect.height < 160) topInset = Math.max(topInset, rect.bottom);
    }
    for (const el of document.querySelectorAll('button,a,[role="button"]')) {
      if (root.contains(el) || !/^(manage app|hosted with streamlit|made with streamlit)$/i.test(el.textContent.trim())) continue;
      const rect = el.getBoundingClientRect();
      if (rect.width && rect.height && rect.top > height * .6 && rect.bottom <= height + 2) bottomInset = Math.max(bottomInset, height - rect.top);
    }
    const viewport = window.visualViewport;
    if (viewport) bottomInset = Math.max(bottomInset, height - viewport.height - viewport.offsetTop);
    document.documentElement.style.setProperty('--quiz-host-top', Math.ceil(topInset) + 'px');
    document.documentElement.style.setProperty('--quiz-host-bottom', Math.ceil(bottomInset) + 'px');
  }
  const scheduleInsets = () => {if (!layoutFrame) layoutFrame = requestAnimationFrame(updateInsets);};
  updateInsets();
  const resizeObserver = new ResizeObserver(scheduleInsets);
  document.querySelectorAll('[data-testid="stHeader"],[data-testid="stToolbar"]').forEach(el=>resizeObserver.observe(el));
  const mutations = new MutationObserver(scheduleInsets);
  mutations.observe(document.body, {childList:true,subtree:true});
  window.addEventListener('resize', scheduleInsets);
  window.visualViewport?.addEventListener('resize', scheduleInsets);
  window.visualViewport?.addEventListener('scroll', scheduleInsets);

  // Replay only for the initial page and a submitted student search, not filters.
  let shineTimer = null;
  const glints = new Set();
  const shineToken = data?.shineToken ?? 0;
  async function playGlint(target, duration) {
    if (!target) return true;
    const overlay = document.createElement('span');
    overlay.className = 'quiz-gold-glint';
    overlay.textContent = target.textContent;
    overlay.setAttribute('aria-hidden', 'true');
    target.append(overlay);
    const width = target.getBoundingClientRect().width;
    // Decreasing pixel coordinates move the highlight unambiguously right to left.
    const animation = overlay.animate(
      [{backgroundPosition:(width * .1) + 'px 0px'}, {backgroundPosition:(-width * 1.65) + 'px 0px'}],
      {duration, easing:'linear', fill:'both'}
    );
    const item = {overlay, animation};
    glints.add(item);
    try {await animation.finished; return true;}
    catch (_) {return false;}
    finally {overlay.remove();glints.delete(item);}
  }
  if (window.__quizShineToken !== shineToken) {
    window.__quizShineToken = shineToken;
    if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      shineTimer = setTimeout(async () => {
        const finished = await playGlint(document.querySelector('[data-quiz-shine="title"]'), 800);
        if (finished) await playGlint(document.querySelector('[data-quiz-shine="credit"]'), 600);
      }, 1000);
    }
  }

  root.querySelector('[data-empty]').hidden = reports.length > 0;
  root.querySelector('[data-picker]').hidden = reports.length < 2;
  [share,copyButton,pdf].forEach(el=>el.hidden=!reports.length);
  select.replaceChildren();
  reports.forEach((report,index)=>{const option=document.createElement('option');option.value=String(index);option.textContent=report.title;select.append(option);});
  function updatePdf(){if(reports[selected]) pdf.href='data:application/pdf;base64,'+reports[selected].pdf;}
  updatePdf();
  select.onchange=()=>{selected=Number(select.value);feedback.textContent='';updatePdf();};
  top.onclick=()=>{
    menu.hidden=true;plus.setAttribute('aria-expanded','false');
    const input=document.querySelector('input[aria-label="Student Number"],input[aria-label="Name or Student Number"]');
    if(input){input.scrollIntoView({behavior:'smooth',block:'center'});input.focus({preventScroll:true});}
    else {document.querySelector('[data-testid="stMain"]')?.scrollTo({top:0,behavior:'smooth'});window.scrollTo({top:0,behavior:'smooth'});}
  };
  plus.onclick=()=>{menu.hidden=!menu.hidden;plus.setAttribute('aria-expanded',String(!menu.hidden));};
  async function copy(){
    if(!reports[selected])return;
    const text=reports[selected].text;
    try{await navigator.clipboard.writeText(text);feedback.textContent='Report copied.';}
    catch(_){let area=menu.querySelector('textarea');if(!area){area=document.createElement('textarea');area.readOnly=true;area.setAttribute('aria-label','Report text to copy');menu.append(area);}area.value=text;area.focus();area.select();feedback.textContent=document.execCommand('copy')?'Report copied.':'Select and copy the report below.';}
  }
  copyButton.onclick=copy;
  share.onclick=async()=>{if(!reports[selected])return;if(navigator.share){try{await navigator.share({title:'Quiz Status',text:reports[selected].text});}catch(e){if(e.name!=='AbortError')await copy();}}else await copy();};
  const onKey=e=>{if(e.key==='Escape'&&!menu.hidden){menu.hidden=true;plus.setAttribute('aria-expanded','false');plus.focus();}};
  document.addEventListener('keydown',onKey);
  return ()=>{
    if(shineTimer!==null)clearTimeout(shineTimer);
    glints.forEach(({overlay,animation})=>{animation.cancel();overlay.remove();});
    document.removeEventListener('keydown',onKey);
    window.removeEventListener('resize',scheduleInsets);
    window.visualViewport?.removeEventListener('resize',scheduleInsets);
    window.visualViewport?.removeEventListener('scroll',scheduleInsets);
    resizeObserver.disconnect();mutations.disconnect();
    if(layoutFrame)cancelAnimationFrame(layoutFrame);
    root.remove();
  };
}
'''

_actions = component('quiz_mobile_actions', html=HTML, css=CSS, js=JS)


def render_actions(reports, *, shine_token=0):
    _actions(data={'reports': reports, 'shineToken': shine_token}, key='quiz_mobile_actions', height=0, isolate_styles=False)
