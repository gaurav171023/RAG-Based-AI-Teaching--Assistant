const form = document.getElementById('composer');
const input = document.getElementById('question');
const messages = document.getElementById('messages');

function addMessage(text, who='bot', meta=''){
  const el = document.createElement('div');
  el.className = 'msg ' + (who==='user' ? 'user' : 'bot');
  if(meta) el.innerHTML = `<div class="meta">${meta}</div>` + `<div class="body">${text.replace(/\n/g,'<br>')}</div>`;
  else el.innerHTML = `<div class="body">${text.replace(/\n/g,'<br>')}</div>`;
  messages.appendChild(el);
  messages.scrollTop = messages.scrollHeight;
}

// create a typing indicator element
function addTyping(){
  const el = document.createElement('div');
  el.className = 'msg bot typing-msg';
  el.innerHTML = '<div class="meta">Assistant</div><div class="body typing"><span class="dot"></span><span class="dot"></span><span class="dot"></span></div>';
  messages.appendChild(el);
  messages.scrollTop = messages.scrollHeight;
  return el;
}

form.addEventListener('submit', async (e) =>{
  e.preventDefault();
  const q = input.value.trim();
  if(!q) return;
  addMessage(q,'user');
  input.value='';
  const typingEl = addTyping();
  try{
    const res = await fetch('/ask',{method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({question:q})});
    const data = await res.json();
    // remove typing indicator
    if(typingEl) typingEl.remove();
    if(data.error){
      addMessage('Error: '+data.error,'bot');
    }else{
      addMessage(data.answer,'bot');
      if(data.results && data.results.length){
        data.results.slice(0,3).forEach(r =>{
          const snippet = `${r.title} (video ${r.number} @ ${Math.round(r.start)}s): ${r.text}`;
          if(r.link){
            addMessage(snippet + `<br><a href="${r.link}" target="_blank" style="color: #6ee7b7; font-weight:600;">Watch</a>`,'bot','Source');
          }else{
            addMessage(snippet,'bot','Source');
          }
        });
      }
    }
  }catch(err){
    if(typingEl) typingEl.remove();
    addMessage('Network error: '+err.message,'bot');
  }
});

// make chips clickable
document.querySelectorAll('.chip').forEach(c =>{
  c.addEventListener('click', ()=>{
    input.value = c.textContent.trim();
    form.dispatchEvent(new Event('submit', {cancelable:true}));
  })
});
