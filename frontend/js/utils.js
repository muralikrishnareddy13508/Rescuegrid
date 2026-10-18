// RESCUEGRID - utils.js: Search/filter helpers
// Contains: filterRows, searchRows, filterGeneric

function filterRows(q){document.querySelectorAll('tr[data-search]').forEach(r=>r.style.display=r.dataset.search.includes(q.toLowerCase())?'':'none')}

function searchRows(q){document.querySelectorAll('tr[data-search]').forEach(r=>r.style.display=r.dataset.search.includes(q.toLowerCase())?'':'none')}

function filterGeneric(q,id){document.querySelectorAll('#'+id+' [data-search]').forEach(r=>r.style.display=r.dataset.search.includes(q.toLowerCase())?'':'none')}
