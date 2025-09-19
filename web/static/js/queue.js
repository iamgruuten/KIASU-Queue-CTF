
const socket = io("/", {transports:["websocket"]});
const qCounter = document.getElementById("queue-counter");
const joinBtn = document.getElementById("join-btn");
const yourPosWrapper = document.getElementById("your-pos-wrapper");
const yourPos = document.getElementById("your-pos");

function animateNumber(el, from, to){
  gsap.fromTo(el,{innerText:from},{innerText:to, duration:1.2, ease:"power2.out", snap:{innerText:1}});
}

socket.on("queue-size", data=>{
  const current = parseInt(qCounter.innerText || "0");
  if(data.max>current) animateNumber(qCounter,current,data.max);
});

socket.on("position-update", data=>{
  yourPosWrapper.classList.remove("invisible");
  animateNumber(yourPos, parseInt(yourPos.innerText||"0"), data.pos);
  if(data.pos===1){
    const audio = new Audio("/static/sounds/win.mp3");
    audio.play().catch(()=>{});
    gsap.to(yourPos,{scale:1.3,yoyo:true,repeat:3,duration:0.3});
  }
});

if(joinBtn){
  joinBtn.addEventListener("click", ()=>{
    fetch("/queue-position").then(r=>r.json()).then(d=>{
      socket.emit("join");
      socket.emit("client-ready");
      yourPosWrapper.classList.remove("invisible");
      animateNumber(yourPos,0,d.position);
    });
  });
}
