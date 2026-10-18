// RESCUEGRID - state.js: App data and sidebar menu list
// Contains: state, navItems, demoRecipients

const state={page:'home',authTab:'signin',user:'',authenticated:false,donations:[
{id:1,food:'Cooked Meals',category:'Cooked Meals',emoji:'🍲',qty:'50 kg',expiry:'Today, 2 PM',recipient:'Sunrise School Kitchen',distance:'3.2 km',score:92,status:'Completed'},
{id:2,food:'Bakery Items',category:'Bakery Items',emoji:'🥐',qty:'30 kg',expiry:'Today, 4 PM',recipient:'Riverside Community Kitchen',distance:'5.6 km',score:87,status:'Accepted'},
{id:3,food:'Fruits & Vegetables',category:'Fruits & Vegetables',emoji:'🥗',qty:'40 kg',expiry:'Tomorrow, 9 AM',recipient:'Greenfield Family Pantry',distance:'7.1 km',score:81,status:'Matched'},
{id:4,food:'Dairy Products',category:'Dairy Products',emoji:'🥛',qty:'20 kg',expiry:'Today, 6 PM',recipient:null,distance:'—',score:null,status:'Safety cleared'},
{id:5,food:'Prepared Sandwiches',category:'Packaged Food',emoji:'🥪',qty:'15 kg',expiry:'Today, 5 PM',recipient:null,distance:'—',score:null,status:'Safety review',safetyNote:'Missing answer: safe temperature.'}],history:[],chat:[{who:'bot',text:'Hello! I can explain donation priorities, suggest recipients, and help you plan a pickup. What would you like to know?'}],formStep:1};

const navItems=[['dashboard','▦','Dashboard'],['donate','♧','Donate Food'],['matching','⇄','Smart Matching'],['recipients','♙','Recipients'],['impact','◒','Impact'],['reports','▤','Reports'],['settings','⚙','Settings']];

const demoRecipients=[['Sunrise School Kitchen','School meal program','3.2 km','🍲'],['Riverside Community Kitchen','Community kitchen','5.6 km','♡'],['Greenfield Family Pantry','Family food support','7.1 km','♧'],['Open Door Community Center','Community center','8.4 km','🤝']];
