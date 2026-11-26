import {readFileSync} from 'node:fs';
import assert from 'node:assert/strict';
const source=readFileSync(new URL('../mobile_actions.py',import.meta.url),'utf8');
const snippet=source.slice(source.indexOf('  // Student numbers stay text'),source.indexOf('  // Replay only'));
function setup(touch=1,coarse=false){
  class Input{
    constructor(label='Student Number'){this.label=label;this._value='';this.attrs={};this.selectionStart=0;this.selectionEnd=0;}
    get value(){return this._value} set value(v){this._value=v}
    matches(selector){return this.label==='Student Number'&&selector==='input[aria-label="Student Number"]'}
    setAttribute(k,v){this.attrs[k]=v}
    setSelectionRange(start,end){this.selectionStart=start;this.selectionEnd=end}
    dispatchEvent(event){handlers[event.type]?.({...event,target:this});this.sentValue=this.value}
  }
  const input=new Input(),handlers={},document={body:{},querySelectorAll:()=>[input],addEventListener:(name,handler)=>handlers[name]=handler};
  class Observer{constructor(fn){this.fn=fn}observe(){this.fn()}}
  const window={matchMedia:()=>({matches:coarse})};
  new Function('navigator','window','document','HTMLInputElement','MutationObserver','Event',snippet)({maxTouchPoints:touch},window,document,Input,Observer,class{constructor(type,options){this.type=type;Object.assign(this,options)}});
  return{input,handlers,Input};
}
for(const [touch,coarse] of [[1,false],[5,false],[0,true]]){
 const{input,handlers,Input}=setup(touch,coarse);
 assert.equal(input.attrs.inputmode,'numeric');assert.equal(input.attrs.pattern,'[0-9]*');
 input.value='0012';input.setSelectionRange(4,4);handlers.input({target:input});assert.equal(input.value,'0012');
 let blocked=false;handlers.beforeinput({target:input,inputType:'insertText',data:'e',preventDefault(){blocked=true}});assert.ok(blocked);
 input.value='0a01-2.3';input.setSelectionRange(8,8);handlers.input({target:input});assert.equal(input.value,'00123');assert.equal(input.selectionStart,5);
 input.value='0012';input.setSelectionRange(2,4);blocked=false;
 handlers.paste({target:input,clipboardData:{getData:()=> 'A 535-x'},preventDefault(){blocked=true}});
 assert.ok(blocked);assert.equal(input.value,'00535');assert.equal(input.sentValue,'00535');
 input.value='0012';input.setSelectionRange(1,3);handlers.paste({target:input,clipboardData:{getData:()=> 'letters'},preventDefault(){}});assert.equal(input.value,'0012');
 const teacher=new Input('Name or Student Number');teacher.value='Dylan R';handlers.input({target:teacher});assert.equal(teacher.value,'Dylan R');
}
const desktop=setup(0,false);assert.equal(desktop.input.attrs.inputmode,undefined);desktop.input.value='abc';desktop.handlers.input({target:desktop.input});assert.equal(desktop.input.value,'abc');
console.log('PASS: phone/tablet keypad, digits-only typing and paste, leading zeroes, React input event, teacher search and desktop unchanged.');
