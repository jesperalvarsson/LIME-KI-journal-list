/* Enough DOM for the page's top-level code to run under node. The page is
   tested as shipped - the script is read out of dist/ and evaluated - so a
   test can never pass against a copy that has drifted from the built file. */
function el(){
  const e = {
    textContent:"", innerHTML:"", value:"", hidden:false, dataset:{}, style:{},
    classList:{add(){},remove(){},toggle(){},contains(){return false}},
    addEventListener(){}, removeEventListener(){},
    setAttribute(k,v){ this["_"+k]=v }, getAttribute(k){ return this["_"+k]??null },
    querySelector(){ return el() }, querySelectorAll(){ return [] },
    appendChild(){}, focus(){}, scrollIntoView(){},
  };
  return e;
}
global.document = {
  documentElement: el(),
  getElementById(){ return el() },
  querySelector(){ return el() },
  querySelectorAll(){ return [] },
  createElement(){ return el() },
};
global.matchMedia = () => ({ matches:false, addEventListener(){}, addListener(){} });
global.localStorage = { getItem(){ return null }, setItem(){}, removeItem(){} };
global.window = global;
