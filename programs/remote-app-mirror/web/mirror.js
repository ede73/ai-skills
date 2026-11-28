const img=document.querySelector('#frame'), focus=document.querySelector('#focus'), viewport=document.querySelector('main');
let busy=false,last='',zoom=1,panX=0,panY=0,touchGesture=null;
const activePointers=new Map(),MIN_ZOOM=1,MAX_ZOOM=6,MOVE_THRESHOLD=5;
function refresh(){if(!busy){busy=true;img.src='/frame.jpg?'+Date.now();}}
img.onload=()=>busy=false;img.onerror=()=>busy=false;refresh();setInterval(refresh,450);
function send(data){fetch('/input',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)}).catch(()=>{});}
function pos(e){
  const r=viewport.getBoundingClientRect(),cx=r.left+r.width/2,cy=r.top+r.height/2;
  const x=(e.clientX-cx-panX)/zoom+img.offsetWidth/2;
  const y=(e.clientY-cy-panY)/zoom+img.offsetHeight/2;
  return{x:x/img.offsetWidth,y:y/img.offsetHeight};
}
function applyTransform(){
  const limitX=Math.max(0,(img.offsetWidth*zoom-viewport.clientWidth)/2);
  const limitY=Math.max(0,(img.offsetHeight*zoom-viewport.clientHeight)/2);
  panX=Math.max(-limitX,Math.min(limitX,panX));panY=Math.max(-limitY,Math.min(limitY,panY));
  img.style.setProperty('--zoom',zoom);img.style.setProperty('--pan-x',panX+'px');img.style.setProperty('--pan-y',panY+'px');
}
function midpoint(a,b){return{x:(a.x+b.x)/2,y:(a.y+b.y)/2};}
function distance(a,b){return Math.hypot(a.x-b.x,a.y-b.y);}
function zoomAround(nextZoom,oldZoom,oldPanX,oldPanY,oldPoint,newPoint){
  const bounds=viewport.getBoundingClientRect(),cx=bounds.left+bounds.width/2,cy=bounds.top+bounds.height/2,ratio=nextZoom/oldZoom;
  panX=newPoint.x-cx-(oldPoint.x-cx-oldPanX)*ratio;
  panY=newPoint.y-cy-(oldPoint.y-cy-oldPanY)*ratio;
  zoom=nextZoom;applyTransform();
}
function beginPinch(){
  const [a,b]=Array.from(activePointers.values()).slice(0,2),mid=midpoint(a,b);
  touchGesture.pinch={distance:Math.max(1,distance(a,b)),mid,zoom,panX,panY};
  touchGesture.moved=true;
}
function updatePinch(){
  const [a,b]=Array.from(activePointers.values()).slice(0,2),pinch=touchGesture.pinch;
  if(!pinch)return;
  const mid=midpoint(a,b),nextZoom=Math.max(MIN_ZOOM,Math.min(MAX_ZOOM,pinch.zoom*distance(a,b)/pinch.distance));
  zoomAround(nextZoom,pinch.zoom,pinch.panX,pinch.panY,pinch.mid,mid);
}
img.addEventListener('pointerdown',e=>{
  e.preventDefault();img.setPointerCapture(e.pointerId);
  if(activePointers.size===0)touchGesture={moved:false,pinch:null};
  activePointers.set(e.pointerId,{x:e.clientX,y:e.clientY,startX:e.clientX,startY:e.clientY,button:e.button});
  if(activePointers.size===2)beginPinch();
});
img.addEventListener('pointermove',e=>{
  const point=activePointers.get(e.pointerId);if(!point)return;
  const dx=e.clientX-point.x,dy=e.clientY-point.y;point.x=e.clientX;point.y=e.clientY;
  if(activePointers.size>=2){if(!touchGesture.pinch)beginPinch();updatePinch();return;}
  if(!touchGesture.moved&&Math.hypot(e.clientX-point.startX,e.clientY-point.startY)>MOVE_THRESHOLD)touchGesture.moved=true;
  if(touchGesture.moved){panX+=dx;panY+=dy;applyTransform();}
});
function finishPointer(e){
  const point=activePointers.get(e.pointerId);if(!point)return;
  point.x=e.clientX;point.y=e.clientY;
  if(activePointers.size===1&&!touchGesture.moved){
    const r=img.getBoundingClientRect();
    if(e.clientX>=r.left&&e.clientX<=r.right&&e.clientY>=r.top&&e.clientY<=r.bottom){
      focus.focus({preventScroll:true});const p=pos(e),button=point.button;send({kind:'down',...p,button});send({kind:'up',...p,button});
    }
  }
  activePointers.delete(e.pointerId);
  if(activePointers.size===0)touchGesture=null;
}
img.addEventListener('pointerup',e=>{e.preventDefault();finishPointer(e);});
img.addEventListener('pointercancel',e=>{activePointers.delete(e.pointerId);if(activePointers.size===0)touchGesture=null;});
document.addEventListener('wheel',e=>{
  const r=img.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)return;
  e.preventDefault();
  if(e.ctrlKey){const next=Math.max(MIN_ZOOM,Math.min(MAX_ZOOM,zoom*Math.exp(-e.deltaY*.002)));zoomAround(next,zoom,panX,panY,{x:e.clientX,y:e.clientY},{x:e.clientX,y:e.clientY});}
  else send({kind:'scroll',...pos(e),dx:e.deltaX,dy:e.deltaY});
},{capture:true,passive:false});
focus.addEventListener('keydown',e=>{const keys={Backspace:'backspace',Enter:'enter',Tab:'tab',Escape:'escape',ArrowUp:'up',ArrowDown:'down',ArrowLeft:'left',ArrowRight:'right',Delete:'delete'};if(keys[e.key]){e.preventDefault();send({kind:'key',key:keys[e.key],mods:{shift:e.shiftKey,ctrl:e.ctrlKey,alt:e.altKey,meta:e.metaKey}});}});
focus.addEventListener('input',e=>{const v=focus.value;let added=v.startsWith(last)?v.slice(last.length):v;if(e.inputType==='insertFromPaste')added=e.data||added;if(added)send({kind:'text',text:added});last='';focus.value='';});
focus.addEventListener('beforeinput',()=>{last='';});
