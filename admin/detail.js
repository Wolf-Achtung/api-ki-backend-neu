(function(){
  function qs(k, d){ const u=new URL(location.href); return u.searchParams.get(k) || d; }
  function apiBase(){ const m=document.querySelector('meta[name="api-base"]'); return (m && m.content) || '/api'; }
  function token(){ try{ return localStorage.getItem('jwt') || ''; }catch(_){ return ''; } }
  async function api(path, opts){
    const headers = Object.assign({ 'Content-Type': 'application/json' }, (opts && opts.headers)||{});
    const t = token(); if (t) headers.Authorization = 'Bearer ' + t;
    const res = await fetch(apiBase() + path, Object.assign({}, opts, { headers }));
    const ct = res.headers.get('content-type') || '';
    const data = ct.includes('application/json') ? await res.json() : await res.text();
    if (!res.ok) throw new Error((data && data.detail) || res.statusText);
    return data;
  }
  function fmtDate(x){ if (!x) return '–'; try{ return new Date(x).toLocaleString('de-DE'); }catch(_){ return x; } }

  function setupTabs(){
    document.querySelectorAll('.tab').forEach(function(b){
      b.addEventListener('click', function(){
        document.querySelectorAll('.tab').forEach(tb=>tb.classList.remove('active'));
        document.querySelectorAll('.tabpane').forEach(p=>p.classList.remove('active'));
        b.classList.add('active');
        const id = 'tab-' + b.getAttribute('data-tab');
        const pane = document.getElementById(id);
        if (pane) pane.classList.add('active');
      });
    });
  }

  async function loadAll(){
    const briefingId = qs('briefing', '');
    if (!briefingId){ alert('Kein Briefing angegeben.'); return; }

    // Overview + Briefing
    const b = await api('/admin/briefings/' + briefingId);
    document.getElementById('ov-briefing').textContent = b.briefing.id;
    document.getElementById('ov-user').textContent = (b.briefing.user && (b.briefing.user.email || b.briefing.user.id)) || '–';
    document.getElementById('briefing-json').textContent = JSON.stringify(b.briefing, null, 2);
    document.getElementById('btn-export').href = apiBase() + '/admin/briefings/' + briefingId + '/export.zip';

    // Latest analysis
    let latest = await api('/admin/briefings/' + briefingId + '/latest-analysis');
    if (latest && latest.ok && latest.analysis){
      document.getElementById('ov-analysis').textContent = latest.analysis.id + ' (' + fmtDate(latest.analysis.created_at) + ')';
      // Load HTML preview
      const iframe = document.getElementById('analysis-frame');
      try{
        const html = await fetch(apiBase() + '/admin/analyses/' + latest.analysis.id + '/html', {
          headers: (token()? {Authorization:'Bearer '+token()} : {})
        }).then(r=>r.text());
        iframe.srcdoc = html;
      }catch(e){
        iframe.srcdoc = '<p style="padding:10px;color:#b00">Konnte Analyse‑HTML nicht laden: ' + (e.message||e) + '</p>';
      }
    } else {
      document.getElementById('ov-analysis').textContent = '–';
      document.getElementById('analysis-frame').srcdoc = '<p style="padding:10px;">Keine Analyse vorhanden.</p>';
    }

    // Reports for briefing
    const reps = await api('/admin/briefings/' + briefingId + '/reports');
    const host = document.getElementById('reports-list');
    if (reps.rows && reps.rows.length){
      const items = reps.rows.map(function(r){
        const link = r.pdf_url ? '<a class="btn-link" href="'+r.pdf_url+'" target="_blank">PDF öffnen</a>' :
                                  '<span class="muted">(PDF intern gespeichert – im Export enthalten, falls aktiviert)</span>';
        return '<div class="rep-item">Report #'+r.id+' – '+fmtDate(r.created_at)+' · '+ link +'</div>';
      });
      host.innerHTML = items.join('');
    } else {
      host.textContent = 'Kein Report vorhanden.';
    }

    // Rerun button
    document.getElementById('btn-rerun').addEventListener('click', async function(){
      this.disabled = true;
      try{
        await api('/admin/briefings/' + briefingId + '/rerun', { method: 'POST', body: '{}' });
        alert('Analyse/Report wurde neu angestoßen. Aktualisieren Sie die Ansicht in 1–2 Minuten.');
      }catch(e){
        alert('Fehler: ' + (e.message||e));
      }finally{
        this.disabled = false;
      }
    });
  }

  document.getElementById('logout').addEventListener('click', function(){ localStorage.removeItem('jwt'); location.href='/login.html'; });
  if (!token()) { location.href='/login.html'; }
  setupTabs();
  loadAll().catch(function(e){ console.error(e); alert('Ladevorgang fehlgeschlagen: ' + (e.message||e)); });
})();