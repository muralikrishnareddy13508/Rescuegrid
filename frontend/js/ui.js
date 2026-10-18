// RESCUEGRID - ui.js: Shared building blocks: logo, header, sidebar, buttons, toast
// Contains: logo, brand, btn, header, sidebar, mobileNav, pageHead, toast

function logo(){return `<svg class="logo" viewBox="0 0 64 64" aria-label="RescueGrid logo"><path d="M32 3 57 13v19c0 14-10 23-25 29C17 55 7 46 7 32V13Z" fill="#236b50"/><path d="M32 8 52 16v16c0 11-8 19-20 25C20 51 12 43 12 32V16Z" fill="#f5d98d"/><path d="M32 12 48 19v13c0 9-6 16-16 21-10-5-16-12-16-21V19Z" fill="#236b50"/><path d="M22 39V24l10-5 10 5v15l-10 5Z" fill="none" stroke="#fff8df" stroke-width="2.4"/><path d="M27 31h10M32 26v10" stroke="#fff8df" stroke-width="2.4" stroke-linecap="round"/></svg>`}

function brand(){return `<div class="brand">${logo()}<div class="brand-text">RESCUEGRID<small>GOOD FOOD. BETTER FUTURES.</small></div></div>`}

function btn(text,action,cls=''){return `<button class="btn ${cls}" onclick="${action}">${text}</button>`}

function header(){return `<header class="topbar">${brand()}<nav class="nav"><a href="#how" onclick="go('home')">How it works</a><a href="#impact" onclick="go('home')">Our impact</a><a href="#about" onclick="go('home')">About</a>${state.page==='home'?btn('Sign in',`go('auth')`,'secondary small nav-cta'):btn('← Back',`back()`,'secondary small nav-cta')}</nav></header><div class="demo-banner" role="note">Prototype · every name, number and chart on this site is synthetic demo data</div>`}

function sidebar(){return `<aside class="sidebar"><div class="side-brand">${brand()}</div>${navItems.map(([id,ic,label])=>`<button class="side-link ${state.page===id?'active':''}" onclick="go('${id}')"><span>${ic}</span><span class="label">${label}</span></button>`).join('')}<div class="sidebar-bottom"><button class="side-link" onclick="go('home')"><span>↩</span><span class="label">Back to website</span></button></div></aside>`}

function mobileNav(){return `<nav class="mobile-nav">${[['dashboard','▦','Home'],['donate','♧','Donate'],['matching','⇄','Matches'],['recipients','♙','People'],['impact','◒','Impact']].map(([id,ic,l])=>`<button onclick="go('${id}')"><span>${ic}</span>${l}</button>`).join('')}</nav>`}

function pageHead(title,desc){return `<div class="dash-top"><div><button class="back-link" onclick="back()">← Back to previous page</button><h1>${title}</h1><p>${desc}</p></div>${btn('Dashboard ↗',`go('dashboard')`,'secondary small')}</div>`}

function toast(msg){const t=document.getElementById('toast');t.textContent=msg;t.classList.remove('hidden');clearTimeout(window.toastTimer);window.toastTimer=setTimeout(()=>t.classList.add('hidden'),2800)}
