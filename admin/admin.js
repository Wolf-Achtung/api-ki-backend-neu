(function(){
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
  function fmtDate(x){
    if (!x) return '–';
    try{ return new Date(x).toLocaleString('de-DE'); }catch(_){ return x; }
  }
  async function loadOverview(){
    const d = await api('/admin/overview');
    document.getElementById('k-users').textContent = d.totals.users;
    document.getElementById('k-briefings').textContent = d.totals.briefings;
    document.getElementById('k-analyses').textContent = d.totals.analyses;
    document.getElementById('k-reports').textContent = d.totals.reports;
  }
  async function loadBriefings(){
    const q = document.getElementById('q').value.trim();
    const d = await api('/admin/briefings' + (q ? ('?q=' + encodeURIComponent(q)) : ''));
    const tbody = document.getElementById('rows'); tbody.innerHTML='';
    d.rows.forEach(function(r){
      const tr = document.createElement('tr');
      tr.innerHTML = '<td>'+r.id+'</td>' +
                     '<td>'+ (r.user_id || '–') +'</td>' +
                     '<td>'+ fmtDate(r.created_at) +'</td>' +
                     '<td>' +
                       '<a class="btn-link" href="#" data-id="'+r.id+'" data-act="view">Ansehen</a> · ' +
                       '<a class="btn-link" href="'+apiBase()+'/admin/briefings/'+r.id+'/export.zip" target="_blank">Export (.zip)</a>' +
                     '</td>';
      tbody.appendChild(tr);
    });
  }
  async function showBriefing(id){
    const d = await api('/admin/briefings/'+id);
    alert('Briefing #'+id+' für '+ (d.briefing.user && d.briefing.user.email ? d.briefing.user.email : 'User '+d.briefing.user.id));
    // Minimalistisch; auf Wunsch bauen wir eine Detailansicht mit Tabs (Briefing/Analyse/Report)
  }
  document.addEventListener('click', function(e){
    const a = e.target.closest('a[data-act]'); if (!a) return;
    e.preventDefault();
    const id = a.getAttribute('data-id'); const act=a.getAttribute('data-act');
    if (act==='view') showBriefing(id);
  });
  document.getElementById('reload').addEventListener('click', function(){ loadBriefings(); });
  document.getElementById('logout').addEventListener('click', function(){ localStorage.removeItem('jwt'); location.href='/login.html'; });
  // Guard
  if (!token()) { location.href = '/login.html'; return; }
  // Init
  loadOverview().catch(console.error);
  loadBriefings().catch(console.error);
})();