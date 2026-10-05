/* Nordpflege24: menu top left. Works without this file; the script only closes it after a choice, on a click outside and on Escape. */
(function(){
  var m=document.querySelector('.menu'); if(!m) return;
  m.addEventListener('click',function(ev){if(ev.target.closest('a')) m.open=false;});
  document.addEventListener('click',function(ev){if(m.open&&!m.contains(ev.target)) m.open=false;});
  document.addEventListener('keydown',function(ev){if(ev.key==='Escape'&&m.open){m.open=false;m.querySelector('summary').focus();}});
})();
