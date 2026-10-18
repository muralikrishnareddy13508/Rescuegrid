// RESCUEGRID - router.js: Page switching: render, go, back
// Contains: page, render, go, back

function page(){switch(state.page){case'home':return home();case'auth':return auth();case'dashboard':return dashboard();case'donate':return donate();case'matching':return matching();case'recipients':return recipients();case'impact':return impact();case'reports':return reports();case'settings':return settings();default:return dashboard()}}

function render(){document.getElementById('app').innerHTML=page();window.scrollTo({top:0,behavior:'smooth'})}

function go(p){if(['dashboard','donate','matching','recipients','impact','reports','settings'].includes(p)&&!state.authenticated){alert('Please sign in first to access the RescueGrid dashboard.');state.page='auth';state.stack=['home','auth'];render();return}if(state.page!==p){state.previous=state.page;state.page=p;state.stack=state.stack||[];state.stack.push(p)}render()}

function back(){if(state.stack&&state.stack.length>1){state.stack.pop();state.page=state.stack[state.stack.length-1]}else if(state.page==='auth')state.page='home';else if(state.page!=='dashboard')state.page='dashboard';else state.page='home';render()}
