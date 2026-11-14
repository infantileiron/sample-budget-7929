// 轻量 CSV 解析：支持引号、逗号转义与 CRLF；表头中英文均可，统一映射为后端字段。
const HEADER_MAP:Record<string,string>={"档号":"archive_no","archive_no":"archive_no","修订号":"revision","revision":"revision","状态":"status","status":"status","有效或作废状态":"status"};
export interface RegistryCsvRow{[key:string]:string;archive_no:string;revision:string;status:string}
function splitLine(line:string):string[]{
 const out:string[]=[];let cur="",inQuotes=false;
 for(let i=0;i<line.length;i++){
  const ch=line[i];
  if(ch==='"'){
   if(inQuotes&&line[i+1]==='"'){cur+='"';i++}
   else inQuotes=!inQuotes;
  }else if(ch===","&&!inQuotes){out.push(cur);cur=""}
  else cur+=ch;
 }
 out.push(cur);return out.map(v=>v.trim());
}
export function parseRegistryCsv(text:string):RegistryCsvRow[]{
 const lines=text.replace(/^﻿/,"").split(/\r?\n/).filter(l=>l.trim().length>0);
 if(lines.length<2)throw new Error("CSV 需要表头行和至少一行数据");
 const headers=splitLine(lines[0]).map(h=>HEADER_MAP[h.toLowerCase()]??HEADER_MAP[h]??h);
 const idx=(key:string)=>headers.indexOf(key);
 const no=idx("archive_no"),rev=idx("revision"),st=idx("status");
 if(no<0||rev<0||st<0)throw new Error("表头须包含 档号/修订号/状态（或 archive_no/revision/status）");
 return lines.slice(1).map(line=>{
  const cells=splitLine(line);
  return {archive_no:cells[no]??"",revision:cells[rev]??"",status:cells[st]??""};
 });
}
