/* Nordpflege24: question funnel (Pflege / Job), postcode entry, photo fallbacks. No dependencies. */
(function(){
  var PHONE='040 65 39 04 31';
  /* Form service: form.taxi (company in Austria, servers in Germany). Paste the form URL from the form.taxi account here,
     e.g. 'https://form.taxi/s/abc123'. While it is empty, or off the live site, the funnel runs as a preview and sends nothing. */
  var FORM_ENDPOINT='';
  var LIVE=!!FORM_ENDPOINT&&/(^|\.)nordpflege24\.de$|\.github\.io$/.test(location.hostname);

  var FLOWS={
    pflege:{
      form:'pflege-anfrage',
      hero:{
        h1:'Pflege finden. Im Norden.',
        lead:'Sie sagen uns in 30 Sekunden, was gebraucht wird. Wir finden einen Pflegedienst mit freier Kapazität und rufen innerhalb von 24 Stunden zurück.',
        promises:['Unverbindlich','Ohne Anmeldung','Rückruf in 24 Stunden','Keine Weitergabe ohne Ihr Okay']
      },
      steps:[
        {key:'fuer',type:'single',q:'Für wen suchen Sie Pflege?',opts:[{v:'Für einen Angehörigen'},{v:'Für mich selbst'}]},
        {key:'bedarf',type:'multi',q:'Was wird gebraucht?',hint:'Mehrere Antworten sind möglich.',opts:[
          {v:'Grundpflege',d:'Waschen, Anziehen, Essen'},
          {v:'Behandlungspflege',d:'Medikamente, Wunden, Spritzen'},
          {v:'Hauswirtschaft',d:'Einkauf, Kochen, Reinigung'},
          {v:'Betreuung',d:'Begleitung im Alltag'},
          {v:'Intensivpflege',d:'Beatmung, rund um die Uhr'},
          {v:'Weiß ich noch nicht',d:'Wir klären das am Telefon'}]},
        {key:'ort',type:'ort',q:'Wo wird die Pflege gebraucht?'}
      ],
      contact:{q:'Wohin dürfen wir uns melden?',hint:'Wir rufen innerhalb von 24 Stunden zurück.',submit:'Rückruf anfordern',
        consent:'Ich willige ein, dass Nordpflege24 (RAIT Solution, Hamburg) meine Angaben einschließlich der Angaben zum Pflegebedarf (Gesundheitsdaten) verarbeitet, um mich zurückzurufen und passende Pflegedienste zu suchen. Frage ich für eine andere Person an, ist sie einverstanden oder ich darf sie vertreten. An einen Pflegedienst gehen die Daten erst nach meiner ausdrücklichen Zustimmung. Die Einwilligung kann ich jederzeit widerrufen, zum Beispiel per E-Mail an kontakt@nordpflege24.de.'},
      done:'Wir rufen Sie innerhalb von 24 Stunden zurück unter',
      fail:'Das Senden hat nicht geklappt. Bitte versuchen Sie es noch einmal oder rufen Sie uns an: '
    },
    job:{
      form:'job-anfrage',
      hero:{
        h1:'Dein Job in der Pflege.',
        lead:'Drei Klicks, kein Lebenslauf. Wir kennen viele Pflegedienste im Norden und melden uns innerhalb von 24 Stunden bei dir.',
        promises:['Unverbindlich','Kein Lebenslauf','Rückruf in 24 Stunden','Keine Weitergabe ohne dein Okay']
      },
      steps:[
        {key:'ausbildung',type:'single',q:'Was ist deine Ausbildung?',opts:[
          {v:'Pflegefachkraft',d:'Examiniert, 3 Jahre Ausbildung'},
          {v:'Pflegehelfer oder Pflegeassistenz'},
          {v:'Betreuung oder Hauswirtschaft'},
          {v:'Quereinstieg',d:'Noch ohne Pflegeausbildung'}]},
        {key:'umfang',type:'single',q:'Wie viel möchtest du arbeiten?',opts:[{v:'Vollzeit'},{v:'Teilzeit'},{v:'Minijob'}]},
        {key:'ort',type:'ort',q:'Wo wohnst du?'}
      ],
      contact:{q:'Wie erreichen wir dich?',hint:'Wir melden uns innerhalb von 24 Stunden.',submit:'Jobs anfragen',
        consent:'Ich willige ein, dass Nordpflege24 (RAIT Solution, Hamburg) meine Angaben verarbeitet, um mich zurückzurufen und mir passende Stellen vorzuschlagen. An einen Arbeitgeber gehen die Daten erst nach meiner ausdrücklichen Zustimmung. Die Einwilligung kann ich jederzeit widerrufen, zum Beispiel per E-Mail an kontakt@nordpflege24.de.'},
      done:'Wir melden uns innerhalb von 24 Stunden bei dir unter',
      fail:'Das Senden hat nicht geklappt. Bitte versuch es noch einmal oder ruf uns an: '
    }
  };

  function check(size){return '<svg width="'+size+'" height="'+size+'" viewBox="0 0 18 18" aria-hidden="true"><path d="M3 9.5 7 13.5 15 4.5" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>';}
  var ARROW='<svg class="go" width="18" height="18" viewBox="0 0 18 18" aria-hidden="true"><path d="M3 9h12M10 4l5 5-5 5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>';

  var state={
    flow:'pflege',
    pos:{pflege:{step:0,done:false},job:{step:0,done:false}},
    answers:{pflege:{},job:{}},
    contact:{vorname:'',nachname:'',telefon:'',email:'',consent:false,agb:false},
    errors:{},
    sending:false,
    sendError:''
  };
  var funnel=document.getElementById('funnel');
  var body=document.getElementById('funnel-body');
  var tabs=Array.prototype.slice.call(funnel.querySelectorAll('.tab'));

  function esc(s){return String(s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
  function ortOk(v){return !!v && v.trim().length>=2;}

  function validate(c){
    var e={};
    if(!c.vorname.trim()) e.vorname='Bitte den Vornamen eintragen.';
    if(!c.nachname.trim()) e.nachname='Bitte den Nachnamen eintragen.';
    if(c.telefon.replace(/\D/g,'').length<6) e.telefon='Bitte eine Telefonnummer eintragen, unter der wir zurückrufen können.';
    if(!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(c.email.trim())) e.email='Diese E-Mail-Adresse ist unvollständig. Beispiel: name@beispiel.de';
    if(!c.consent) e.consent='Bitte die Einwilligung ankreuzen. Ohne sie dürfen wir nicht zurückrufen.';
    if(!c.agb) e.agb='Bitte den AGB zustimmen. Ohne Zustimmung können wir die Anfrage nicht annehmen.';
    return e;
  }

  /* Builds the field set the host receives. Kept separate so it can be checked on its own. */
  function payload(flow){
    var f=FLOWS[flow], a=state.answers[flow], c=state.contact;
    var data={formular:f.form,_gotcha:''};
    f.steps.forEach(function(s){var v=a[s.key];data[s.key]=Array.isArray(v)?v.join(', '):(v||'');});
    data.vorname=c.vorname.trim();data.nachname=c.nachname.trim();data.telefon=c.telefon.trim();data.email=c.email.trim();
    data.einwilligung=c.consent?'ja':'nein';
    /* Proof of consent: the exact wording shown and the moment of the click travel with the request. */
    data.einwilligung_text=f.contact.consent;
    data.einwilligung_zeit=new Date().toISOString();
    data.agb=c.agb?'ja, Stand Oktober 2026':'nein';
    return data;
  }
  function encode(data){
    return Object.keys(data).map(function(k){return encodeURIComponent(k)+'='+encodeURIComponent(data[k]);}).join('&');
  }

  function navView(showNext,disabled){
    var p=state.pos[state.flow];
    if(p.step===0&&!showNext) return '';
    var h='<div class="fnav">';
    if(p.step>0) h+='<button type="button" class="linkbtn" data-act="back">Zurück</button>';
    if(showNext) h+='<button type="button" class="btn" id="next-btn" data-act="next"'+(disabled?' disabled':'')+'>Weiter</button>';
    return h+'</div>';
  }

  function questionView(s,a){
    var h='<h2 class="q" tabindex="-1" data-focus>'+esc(s.q)+'</h2>';
    if(s.hint) h+='<p class="hint">'+esc(s.hint)+'</p>';
    if(s.type==='single'){
      h+='<div class="opts">'+s.opts.map(function(o){
        return '<button type="button" class="opt" data-act="pick" data-val="'+esc(o.v)+'" aria-pressed="'+(a[s.key]===o.v)+'"><span class="opt-t">'+esc(o.v)+(o.d?'<small>'+esc(o.d)+'</small>':'')+'</span>'+ARROW+'</button>';
      }).join('')+'</div>'+navView(false);
    }else if(s.type==='multi'){
      var sel=a[s.key]||[];
      h+='<div class="opts">'+s.opts.map(function(o){
        return '<button type="button" class="opt" data-act="toggle" data-val="'+esc(o.v)+'" aria-pressed="'+(sel.indexOf(o.v)>-1)+'"><span class="tick">'+check(13)+'</span><span class="opt-t">'+esc(o.v)+(o.d?'<small>'+esc(o.d)+'</small>':'')+'</span></button>';
      }).join('')+'</div>'+navView(true,sel.length===0);
    }else{
      h+='<div class="field"><label for="ort-input">PLZ oder Ort</label><input id="ort-input" name="ort" type="text" autocomplete="postal-code" placeholder="z. B. 22043 oder Hamburg" value="'+esc(a.ort||'')+'"></div>';
      h+=navView(true,!ortOk(a.ort));
    }
    return h;
  }

  function fieldView(id,label,type,auto,mode){
    var v=state.contact[id], e=state.errors[id];
    return '<div class="field"><label for="f-'+id+'">'+label+'</label><input id="f-'+id+'" name="'+id+'" type="'+type+'" autocomplete="'+auto+'"'+(mode?' inputmode="'+mode+'"':'')+' value="'+esc(v)+'"'+(e?' aria-invalid="true" aria-describedby="e-'+id+'"':'')+'>'+(e?'<span class="err" id="e-'+id+'">'+esc(e)+'</span>':'')+'</div>';
  }

  function contactView(f,a){
    var sum=f.steps.map(function(s){var v=a[s.key];return Array.isArray(v)?v.join(', '):v;}).filter(Boolean);
    var e=state.errors;
    var h='<h2 class="q" tabindex="-1" data-focus>'+esc(f.contact.q)+'</h2><p class="hint">'+esc(f.contact.hint)+'</p>';
    h+='<p class="summary">'+sum.map(esc).join(' · ')+'</p>';
    h+='<form id="contact-form" novalidate><div class="two">'+fieldView('vorname','Vorname','text','given-name')+fieldView('nachname','Nachname','text','family-name')+'</div>';
    h+='<div class="two">'+fieldView('telefon','Telefon','tel','tel','tel')+fieldView('email','E-Mail','email','email','email')+'</div>';
    h+='<label class="consent" for="f-consent"><input id="f-consent" name="consent" type="checkbox"'+(state.contact.consent?' checked':'')+(e.consent?' aria-invalid="true" aria-describedby="e-consent"':'')+'><span>'+esc(f.contact.consent)+' Mehr dazu im <a href="datenschutz.html" target="_blank" rel="noopener">Datenschutz</a>.</span></label>';
    if(e.consent) h+='<span class="err" id="e-consent">'+esc(e.consent)+'</span>';
    h+='<label class="consent" for="f-agb"><input id="f-agb" name="agb" type="checkbox"'+(state.contact.agb?' checked':'')+(e.agb?' aria-invalid="true" aria-describedby="e-agb"':'')+'><span>Ich stimme den <a href="agb.html" target="_blank" rel="noopener">AGB</a> zu.</span></label>';
    if(e.agb) h+='<span class="err" id="e-agb">'+esc(e.agb)+'</span>';
    if(state.sendError) h+='<span class="err" role="alert">'+esc(state.sendError)+'</span>';
    h+='<div class="fnav"><button type="button" class="linkbtn" data-act="back">Zurück</button><button type="submit" class="btn"'+(state.sending?' disabled':'')+'>'+esc(state.sending?'Wird gesendet …':f.contact.submit)+'</button></div></form>';
    return h;
  }

  function doneView(f){
    var c=state.contact;
    var h='<div class="done"><span class="done-mark">'+check(28)+'</span><h2 class="q" tabindex="-1" data-focus>Danke, '+esc(c.vorname.trim())+'.</h2><p>'+esc(f.done)+' <strong>'+esc(c.telefon.trim())+'</strong>.</p>';
    if(!LIVE) h+='<p class="note">Vorschau: Diese Anfrage wurde noch nicht versendet. Auf der Live-Seite geht sie per E-Mail an Nordpflege24.</p>';
    return h+'<button type="button" class="btn btn-outline" data-act="reset">Neue Anfrage starten</button></div>';
  }

  function render(focus){
    var f=FLOWS[state.flow], a=state.answers[state.flow], p=state.pos[state.flow];
    tabs.forEach(function(t){t.setAttribute('aria-selected',String(t.getAttribute('data-flow')===state.flow));});
    document.getElementById('hero-h1').textContent=f.hero.h1;
    document.getElementById('hero-lead').textContent=f.hero.lead;
    document.getElementById('hero-promises').innerHTML=f.hero.promises.map(function(t){return '<li>'+check(15)+'<span>'+esc(t)+'</span></li>';}).join('');
    var h;
    if(p.done){h=doneView(f);}
    else{
      var total=f.steps.length+1, n=p.step+1;
      h='<div class="progress"><span>Schritt '+n+' von '+total+'</span><span class="bar" style="--p:'+Math.round(n/total*100)+'%"><i></i></span></div>';
      h+=p.step<f.steps.length?questionView(f.steps[p.step],a):contactView(f,a);
    }
    body.innerHTML=h;
    if(focus){
      var t=body.querySelector('[aria-invalid="true"]')||body.querySelector('[data-focus]');
      if(t){
        t.focus({preventScroll:true});
        if(t.hasAttribute('aria-invalid')&&t.scrollIntoView) t.scrollIntoView({block:'center'});
      }
    }
  }

  function toFunnel(){
    var calm=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    funnel.scrollIntoView({behavior:calm?'auto':'smooth',block:'start'});
  }

  function finish(flow){state.sending=false;state.sendError='';state.pos[flow].done=true;render(true);toFunnel();}

  function send(flow){
    if(!LIVE){finish(flow);return;}
    state.sending=true;state.sendError='';render(false);
    var data=payload(flow), fd=new FormData();
    Object.keys(data).forEach(function(k){fd.append(k,data[k]);});
    fetch(FORM_ENDPOINT,{method:'POST',headers:{'Accept':'application/json'},body:fd})
      .then(function(r){if(!r.ok) throw new Error('HTTP '+r.status);return r.json();})
      .then(function(d){if(!d||d.success===false) throw new Error('rejected');finish(flow);})
      .catch(function(){state.sending=false;state.sendError=FLOWS[flow].fail+PHONE;render(true);});
  }

  body.addEventListener('click',function(ev){
    var b=ev.target.closest('[data-act]'); if(!b||b.disabled) return;
    var f=FLOWS[state.flow], a=state.answers[state.flow], p=state.pos[state.flow], s=f.steps[p.step];
    var act=b.getAttribute('data-act'), val=b.getAttribute('data-val');
    if(act==='pick'){a[s.key]=val;p.step++;render(true);}
    else if(act==='toggle'){
      var sel=a[s.key]||(a[s.key]=[]), i=sel.indexOf(val);
      if(i>-1) sel.splice(i,1); else sel.push(val);
      b.setAttribute('aria-pressed',String(i===-1));
      document.getElementById('next-btn').disabled=sel.length===0;
    }
    else if(act==='next'){p.step++;render(true);}
    else if(act==='back'){state.errors={};state.sendError='';p.step=Math.max(0,p.step-1);render(true);}
    else if(act==='reset'){p.done=false;p.step=0;state.answers[state.flow]={};state.contact.consent=false;state.contact.agb=false;state.errors={};render(true);}
  });

  body.addEventListener('input',function(ev){
    var t=ev.target;
    if(t.id==='ort-input'){
      state.answers[state.flow].ort=t.value;
      document.getElementById('next-btn').disabled=!ortOk(t.value);
      return;
    }
    if(t.name==='consent'||t.name==='agb'){state.contact[t.name]=t.checked;}
    else if(t.name&&Object.prototype.hasOwnProperty.call(state.contact,t.name)){state.contact[t.name]=t.value;}
    else return;
    if(state.errors[t.name]){
      delete state.errors[t.name];
      t.removeAttribute('aria-invalid');
      var old=document.getElementById('e-'+t.name);
      if(old) old.remove();
    }
  });

  body.addEventListener('keydown',function(ev){
    if(ev.key==='Enter'&&ev.target.id==='ort-input'){
      ev.preventDefault();
      if(ortOk(ev.target.value)){state.pos[state.flow].step++;render(true);}
    }
  });

  body.addEventListener('submit',function(ev){
    ev.preventDefault();
    if(state.sending) return;
    state.errors=validate(state.contact);
    if(Object.keys(state.errors).length===0){send(state.flow);}
    else render(true);
  });

  tabs.forEach(function(t){
    t.addEventListener('click',function(){state.flow=t.getAttribute('data-flow');state.errors={};state.sendError='';render(false);});
  });

  document.addEventListener('click',function(ev){
    var st=ev.target.closest('[data-start]');
    if(st){state.flow=st.getAttribute('data-start');state.errors={};state.sendError='';render(true);toFunnel();}
  });

  var plzForm=document.getElementById('plz-form'), plzInput=document.getElementById('plz-input'), plzErr=document.getElementById('plz-err');
  plzForm.addEventListener('submit',function(ev){
    ev.preventDefault();
    var v=plzInput.value.trim();
    if(!ortOk(v)){plzErr.hidden=false;plzInput.focus();return;}
    plzErr.hidden=true;
    state.answers.pflege.ort=v;state.answers.job.ort=v;
    state.flow='pflege';state.errors={};
    if(state.pos.pflege.done){state.pos.pflege.done=false;state.pos.pflege.step=0;}
    render(true);toFunnel();
  });
  plzInput.addEventListener('input',function(){plzErr.hidden=true;});

  /* Photos: every slot starts as a quiet labelled tile; once its file under /images loads, the photo takes over. */
  Array.prototype.forEach.call(document.querySelectorAll('.photo img'),function(img){
    function show(){img.parentNode.classList.remove('is-empty');}
    if(img.complete&&img.naturalWidth) show();
    else img.addEventListener('load',show);
  });

  /* Exposed for a quick check of the field set; not used by the page itself. */
  window.__np24={payload:payload,encode:encode,state:state};

  /* The menu on the legal pages links to index.html#job: open the page with the job questions. */
  if(location.hash==='#job') state.flow='job';

  render(false);
})();
