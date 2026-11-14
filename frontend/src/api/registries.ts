import {request} from "./client";
import type {RegistryDetail} from "../types/domain";
export const fetchRegistry=(lotId:string)=>request<RegistryDetail>(`/lots/${lotId}/registry`);
export const putRegistry=(lotId:string,rows:Record<string,unknown>[])=>request<RegistryDetail>(`/lots/${lotId}/registry`,"PUT",{rows});
