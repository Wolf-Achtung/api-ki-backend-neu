(function(){
  // --- Config ---
  var POLL_INTERVAL_MS = 12000;     // 12s Polling
  var POLL_MAX_ATTEMPTS = 40;       // max ~8 Minuten
  var SANITIZE = true;              // sanitize HTML preview

  function qs(k, d){ var u=new URL(location.href); return u.searchParams.get(k) || d; }
  function apiBase(){ var m=document.querySelector('meta[name="api-base"]'); return (m && m.content) || '/api'; }
  function token(){ try{ return localStorage.getItem('jwt') || ''; }catch(_){ return ''; } }
  async function api(path, opts){
    var headers = Object.assign({ 'Content-Type': 'application/json' }, (opts && opts.headers)||{});
    var t = token(); if (t) headers.Authorization = 'Bearer ' + t;
    var res = await fetch(apiBase() + path, Object.assign({}, opts, { headers }));
    var ct = res.headers.get('content-type') || '';
    var data = ct.includes('application/json') ? await res.json() : await res.text();
    if (!res.ok) throw new Error((data && data.detail) || res.statusText);
    return data;
  }
  function fmtDate(x){ if (!x) return '–'; try{ return new Date(x).toLocaleString('de-DE'); }catch(_){ return x; } }

  // --- Toaster ---
  var toastEl;
  function toast(msg, cls){
    toastEl = toastEl || document.getElementById('toast');
    if (!toastEl) return;
    toastEl.className = 'toast ' + (cls||'');
    toastEl.textContent = msg || '';
    requestAnimationFrame(function(){ toastEl.classList.add('show'); });
    setTimeout(function(){ toastEl.classList.remove('show'); }, 3500);
  }

  // --- Minimal Sanitizer (not a full DOMPurify replacement) ---
  function sanitizeHTML(html){
    if (!SANITIZE || !html) return html || '';
    try{
      // strip scripts & iframes
      html = html.replace(/<script[\s\S]*?>[\s\S]*?<\/script>/gi, '');
      html = html.replace(/<iframe[\s\S]*?>[\s\S]*?<\/iframe>/gi, '');
      // remove on* handlers
      html = html.replace(/ on[a-z]+="[^"]*"/gi, '');
      html = html.replace(/ on[a-z]+='[^']*'/gi, '');
      // neutralize javascript: URLs
      html = html.replace(/href\s*=\s*"(javascript:.*?)"/gi, 'href="#"');
      html = html.replace(/href\s*=\s*'(javascript:.*?)'/gi, "href='#'");
      return html;
    }catch(e){ return html; }
  }

  function setupTabs(){
    document.querySelectorAll('.tab').forEach(function(b){
      b.addEventListener('click', function(){
        document.querySelectorAll('.tab').forEach(function(tb){ tb.classList.remove('active'); });
        document.querySelectorAll('.tabpane').forEach(function(p){ p.classList.remove('active'); });
        b.classList.add('active');
        var id = 'tab-' + b.getAttribute('data-tab');
        var pane = document.getElementById(id);
        if (pane) pane.classList.add('active');
      });
    });
  }

  async function loadAll(){
    var briefingId = qs('briefing', '');
    if (!briefingId){ alert('Kein Briefing angegeben.'); return; }

    // Overview + Briefing
    var b = await api('/admin/briefings/' + briefingId);
    document.getElementById('ov-briefing').textContent = b.briefing.id;
    document.getElementById('ov-user').textContent = (b.briefing.user && (b.briefing.user.email || b.briefing.user.id)) || '–';
    document.getElementById('briefing-json').textContent = JSON.stringify(b.briefing, null, 2);
    document.getElementById('btn-export').href = apiBase() + '/admin/briefings/' + briefingId + '/export.zip';

    await refreshPreviewAndReports(briefingId);
  }

  async function refreshPreviewAndReports(briefingId){
    // Latest analysis
    var latest = await api('/admin/briefings/' + briefingId + '/latest-analysis');
    var iframe = document.getElementById('analysis-frame');
    if (latest && latest.ok && latest.analysis){
      document.getElementById('ov-analysis').textContent = latest.analysis.id + ' (' + fmtDate(latest.analysis.created_at) + ')';
      try{
        var html = await fetch(apiBase() + '/admin/analyses/' + latest.analysis.id + '/html', {
          headers: (token()? {Authorization:'Bearer '+token()} : {})
        }).then(function(r){ return r.text(); });
        iframe.srcdoc = SANITIZE ? sanitizeHTML(html) : html;
      }catch(e){
        iframe.srcdoc = '<p style="padding:10px;color:#b00">Konnte Analyse‑HTML nicht laden: ' + (e.message||e) + '</p>';
      }
    } else {
      document.getElementById('ov-analysis').textContent = '–';
      iframe.srcdoc = '<p style="padding:10px;">Keine Analyse vorhanden.</p>';
    }

    // Reports for briefing
    var reps = await api('/admin/briefings/' + briefingId + '/reports');
    var host = document.getElementById('reports-list');
    if (reps.rows && reps.rows.length){
      var items = reps.rows.map(function(r){
        var link = r.pdf_url ? '<a class="btn-link" href="'+r.pdf_url+'" target="_blank">PDF öffnen</a>' :
                               '<span class="muted">(PDF intern gespeichert – im Export enthalten, falls aktiviert)</span>';
        return '<div class="rep-item">Report #'+r.id+' – '+fmtDate(r.created_at)+' · '+ link +'</div>';
      });
      host.innerHTML = items.join('');
    } else {
      host.textContent = 'Kein Report vorhanden.';
    }
  }

  // --- Polling after rerun ---
  async function pollAfterRerun(briefingId, initialAnalysisId){
    var attempts = 0;
    async function _poll(){
      try{
        var latest = await api('/admin/briefings/' + briefingId + '/latest-analysis');
        var newId = latest && latest.ok && latest.analysis ? latest.analysis.id : null;
        if (newId && newId !== initialAnalysisId){
          toast('✅ Neuer Report erstellt – Vorschau aktualisiert.');
          await refreshPreviewAndReports(briefingId);
          return; // stop polling
        }
      }catch(_){ /* ignore and continue */ }
      if (++attempts < POLL_MAX_ATTEMPTS){
        setTimeout(_poll, POLL_INTERVAL_MS);
      }else{
        toast('⌛ Zeitüberschreitung: Kein neuer Report gefunden.', 'warn');
      }
    }
    setTimeout(_poll, POLL_INTERVAL_MS);
  }

  // --- Wire up page actions ---
  document.getElementById('logout').addEventListener('click', function(){ localStorage.removeItem('jwt'); location.href='/login.html'; });

  function onRerun(){
    var btn = document.getElementById('btn-rerun');
    btn.addEventListener('click', async function(){
      var briefingId = qs('briefing', '');
      if (!briefingId) return;
      btn.disabled = true;
      var latest = await api('/admin/briefings/' + briefingId + '/latest-analysis').catch(function(){ return null; });
      var initialId = latest && latest.ok && latest.analysis ? latest.analysis.id : null;
      try{
        await api('/admin/briefings/' + briefingId + '/rerun', { method: 'POST', body: '{}' });
        toast('🔁 Analyse/Report neu angestoßen …');
        pollAfterRerun(briefingId, initialId);
      }catch(e){
        toast('Fehler beim Neu-Erzeugen: ' + (e.message||e), 'err');
      }finally{
        btn.disabled = false;
      }
    });
  }

  // Guard & init
  if (!token()) { location.href='/login.html'; return; }
  (function init(){
    // Tabs + Load
    document.querySelectorAll('.tab').forEach(function(b){
      b.addEventListener('click', function(){
        document.querySelectorAll('.tab').forEach(function(tb){ tb.classList.remove('active'); });
        document.querySelectorAll('.tabpane').forEach(function(p){ p.classList.remove('active'); });
        b.classList.add('active');
        var id = 'tab-' + b.getAttribute('data-tab'); var pane = document.getElementById(id);
        if (pane) pane.classList.add('active');
      });
    });
    loadAll().catch(function(e){ console.error(e); toast('Ladevorgang fehlgeschlagen: ' + (e.message||e), 'err'); });
    onRerun();
  })();
})();