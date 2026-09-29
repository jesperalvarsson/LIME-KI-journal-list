require("./domshim.js");
const fs=require("fs");
(0,eval)(fs.readFileSync("page.js","utf8")+"\nglobal.__X={norm,J,PFX,fuzzyScore,FUZZ};");
const {norm,J,PFX,fuzzyScore,FUZZ}=global.__X;
function best(q){
  const qt=norm(q).split(" ").filter(Boolean), cand=new Set();
  for(const w of qt) for(const i of (PFX.get(w.slice(0,2))||[])) cand.add(i);
  let b=[0,null];
  for(const i of cand){ const f=fuzzyScore(qt,J[i]); if(f>b[0]||(f===b[0]&&b[1]&&J[i].t.length<b[1].length)) b=[f,J[i].t]; }
  return b;
}
const T=["Lancett","Naure","Lanct","BMJ Opne","Plos medicin","Jorunal of affective disorders",
         "Sucide and life threatening behavior","Acta psychiatrica scandinavia"];
const A=["Journal of Imaginary Studies","Journal of Invented Medicine","Nordic Journal of Nothing",
         "International Journal of Fabrication","Annals of Nowhere","Review of Unreal Biology",
         "Scandinavian Journal of Make Believe","Acta Fictiva"];
const t0=Date.now();
console.log("threshold =",FUZZ);
console.log("\nSHOULD match (real typos):");
let lo=1; for(const q of T){const b=best(q); lo=Math.min(lo,b[0]);
  console.log(("   "+q).padEnd(44), b[0].toFixed(3), (b[0]>=FUZZ?"ok  ":"MISS"), "->", b[1]);}
console.log("\nSHOULD NOT match (absent journals):");
let hi=0; for(const q of A){const b=best(q); hi=Math.max(hi,b[0]);
  console.log(("   "+q).padEnd(44), b[0].toFixed(3), (b[0]<FUZZ?"ok  ":"FALSE POS"), "->", b[1]);}
console.log("\nlowest typo", lo.toFixed(3), " highest absent", hi.toFixed(3),
            " gap", (lo-hi).toFixed(3), " |", ((Date.now()-t0)/(T.length+A.length)).toFixed(1), "ms/query");
