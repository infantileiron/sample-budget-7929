import {ref} from 'vue';
import {fetchRegistry,putRegistry} from '../api/registries';
import type {RegistryDetail} from '../types/domain';
export function registryStore(){
 const detail=ref<RegistryDetail|null>(null);
 const error=ref('');
 const busy=ref(false);
 async function load(lotId:string){
  busy.value=true;
  try{detail.value=await fetchRegistry(lotId);error.value=''}
  catch(e){error.value=(e as Error).message}
  finally{busy.value=false}
 }
 async function importRows(lotId:string,rows:Record<string,unknown>[]){
  detail.value=await putRegistry(lotId,rows);
  return detail.value;
 }
 return {detail,error,busy,load,importRows};
}
