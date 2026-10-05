/* The live site must not be shown inside someone else's frame (the server cannot send this rule for plain HTML files). */
if(/^(www\.)?nordpflege24\.de$/.test(location.hostname)&&window.top!==window.self){
  try{window.top.location=window.location.href;}catch(e){document.documentElement.style.display='none';}
}

/* Nordpflege24: menu top left. Works without this file; the script only closes it after a choice, on a click outside and on Escape. */
(function(){
  var m=document.querySelector('.menu'); if(!m) return;
  m.addEventListener('click',function(ev){if(ev.target.closest('a')) m.open=false;});
  document.addEventListener('click',function(ev){if(m.open&&!m.contains(ev.target)) m.open=false;});
  document.addEventListener('keydown',function(ev){if(ev.key==='Escape'&&m.open){m.open=false;m.querySelector('summary').focus();}});
})();
