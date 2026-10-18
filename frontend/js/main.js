// RESCUEGRID - main.js: Start-up (must load LAST)
// Contains: document.addEventListener, state.stack=

document.addEventListener('keydown',e=>{if(e.altKey&&e.key==='ArrowLeft')back()});

state.stack=['home'];render();
