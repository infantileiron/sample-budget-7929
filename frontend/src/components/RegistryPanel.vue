<script setup lang="ts">
import {ref,computed,watch} from 'vue';
import {lots} from '../stores/lots';
import {canWrite} from '../stores/auth';
import {useTask} from '../hooks/useTask';
import {parseRegistryCsv} from '../utils/csv';
import {registryStore} from '../stores/registries';
import {registryStatusLabels,dispositionLabels} from '../constants/enums';
import Notice from './common/Notice.vue';
import type {RegistryDetailRow,RegistryImportSummary} from '../types/domain';
const selectedLot=ref('');
const parsed=ref<Record<string,unknown>[]>([]);
const fileName=ref('');
const {error,busy,act}=useTask();
const store=registryStore();
const writable=computed(()=>canWrite());
watch(selectedLot,id=>{if(id){store.load(id);parsed.value=[];fileName.value=''}});
function onFile(event:Event){
 const input=event.target as HTMLInputElement;
 const file=input.files?.[0];
 if(!file)return;
 fileName.value=file.name;
 file.text().then(text=>{
  try{parsed.value=parseRegistryCsv(text);error.value=''}
  catch(e){parsed.value=[];error.value=(e as Error).message}
 }).catch(e=>{error.value=(e as Error).message});
}
function submit(){
 if(!selectedLot.value){error.value='请先选择要导入的批次';return}
 act(async()=>{await store.importRows(selectedLot.value,parsed.value);await lots.load()});
}
const summary=computed<RegistryImportSummary|null>(()=>store.detail.value?.last_import?.counts??null);
const groups=computed<{key:'adopted'|'ignored'|'quarantined';rows:RegistryDetailRow[]}[]>(()=>{
 const li=store.detail.value?.last_import;
 if(!li)return[];
 return [{key:'adopted',rows:li.adopted},{key:'ignored',rows:li.ignored},{key:'quarantined',rows:li.quarantined}];
});
const sumOk=computed(()=>{const s=summary.value;return s?s.adopted+s.ignored+s.quarantined===s.input:false});
</script>
<template>
 <section class="registry-panel">
  <p class="eyebrow">PER-DOCUMENT REGISTRY · 逐份底册</p>
  <h2>导入逐份档案底册</h2>
  <p class="method-note">同一档号采用最高修订号；迟到旧版与重复报送忽略不改结果；同版状态矛盾隔离留因；高版本有效记录可恢复作废档案。容量、差错数与抽样只计有效档号，断号和作废档号不会被抽中。未导入底册的批次仍按前缀连续编号。</p>
  <Notice :message="error||store.error.value"/>
  <label>目标批次
   <select v-model="selectedLot">
    <option value="" disabled>请选择批次</option>
    <option v-for="l in lots.items.value" :key="l.id" :value="l.id">{{l.name}} · 登记 {{l.size}} 份<template v-if="l.registry_imported"> · 有效 {{l.valid_count}} / 作废 {{l.void_count}}</template></option>
   </select>
  </label>
  <template v-if="selectedLot">
   <label>底册 CSV（列：档号、修订号、状态；状态填 有效/作废 或 valid/void）
    <input type="file" accept=".csv,text/csv" @change="onFile">
   </label>
   <p v-if="fileName" class="seed-note">已解析 {{fileName}}：{{parsed.length}} 行待导入</p>
   <form v-if="writable" @submit.prevent="submit">
    <button :disabled="busy||!parsed.length">导入并合并底册</button>
   </form>
   <p v-else class="method-note">只读账号可查看底册，导入需分析师权限。</p>
   <div v-if="summary" class="registry-summary" :class="{ok:sumOk}">
    <span>输入 <b>{{summary.input}}</b></span>
    <span>采用 <b>{{summary.adopted}}</b></span>
    <span>忽略 <b>{{summary.ignored}}</b></span>
    <span>隔离 <b>{{summary.quarantined}}</b></span>
    <small>{{sumOk?'三类数量之和等于输入':'计数校验未通过'}}</small>
   </div>
   <div v-for="g in groups" :key="g.key" class="registry-group">
    <h3>{{dispositionLabels[g.key]}} · {{g.rows.length}} 份</h3>
    <div v-if="g.rows.length" class="table-wrap">
     <table>
      <thead><tr><th>行</th><th>档号</th><th>修订号</th><th>状态</th><th>原因</th></tr></thead>
      <tbody>
       <tr v-for="r in g.rows" :key="g.key+'-'+r.row+'-'+r.archive_no">
        <td>{{r.row}}</td><td class="document-id">{{r.archive_no||'—'}}</td><td>{{r.revision??'—'}}</td><td>{{registryStatusLabels[r.status]||r.status||'—'}}</td><td class="reason-cell">{{r.reason}}</td>
       </tr>
      </tbody>
     </table>
    </div>
    <p v-else class="method-note">本类没有记录。</p>
   </div>
   <div v-if="store.detail.value?.imported" class="registry-group">
    <h3>当前生效档号 · 有效 {{store.detail.value.valid_count}} / 作废 {{store.detail.value.void_count}}</h3>
    <div class="table-wrap">
     <table>
      <thead><tr><th>档号</th><th>最高修订</th><th>状态</th></tr></thead>
      <tbody>
       <tr v-for="e in store.detail.value.entries" :key="e.archive_no">
        <td class="document-id">{{e.archive_no}}</td><td>{{e.revision}}</td><td>{{registryStatusLabels[e.status]}}</td>
       </tr>
      </tbody>
     </table>
    </div>
   </div>
  </template>
 </section>
</template>
