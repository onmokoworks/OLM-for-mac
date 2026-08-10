/* One fresh-process PF32 OLMRadialBlur Type-3 row. Companion PS1 only. */
(function(){
 function env(n){return $.getenv(n)||"";} function rd(p){var f=new File(p);f.encoding="UTF-8";if(!f.open("r"))throw Error("open "+p);var s=f.read();f.close();return s;}
 function js(p){return eval("("+rd(p)+")");} function esc(s){return String(s).replace(/\\/g,"\\\\").replace(/"/g,'\\"').replace(/\r/g,"\\r").replace(/\n/g,"\\n");}
 function enc(v){if(v===null||v===undefined)return"null";if(typeof v==="number"||typeof v==="boolean")return String(v);if(typeof v==="string")return'"'+esc(v)+'"';if(v instanceof Array){var a=[];for(var i=0;i<v.length;i++)a.push(enc(v[i]));return"["+a.join(",")+"]";}var q=[];for(var k in v)if(v.hasOwnProperty(k))q.push('"'+esc(k)+'":'+enc(v[k]));return"{"+q.join(",")+"}";}
 function wr(p,v){var f=new File(p);f.encoding="UTF-8";if(!f.open("w"))throw Error("write "+p);f.write(enc(v)+"\n");f.close();}
 function leaves(g,m,a){if(!g||!g.numProperties)return;for(var i=1;i<=g.numProperties;i++){var p=g.property(i);if(p.matchName===m)a.push(p);if(p.numProperties)leaves(p,m,a);}}
 function one(g,m){var a=[];leaves(g,m,a);if(a.length!==1)throw Error("property cardinality "+m+"="+a.length);return a[0];}
 function val(v){if(v instanceof Array){var a=[];for(var i=0;i<v.length;i++)a.push(v[i]);return a;}return v;}
 function same(a,b){if(a instanceof Array&&b instanceof Array){if(a.length!==b.length)return false;for(var i=0;i<a.length;i++)if(Math.abs(Number(a[i])-Number(b[i]))>1e-7)return false;return true;}return Number(a)===Number(b);}
 var root=env("OLMRB_ROOT"),id=env("OLMRB_ROW"),out=env("OLMRB_OUT"),ready=env("OLMRB_READY"),go=env("OLMRB_GO"),result=env("OLMRB_RESULT"),nonce=env("OLMRB_NONCE"),templ=env("OLMRB_TEMPLATE"),summary={status:"error"};
 try{
  if(!root||!id||!out||!ready||!go||!result||!nonce||!templ)throw Error("runner environment incomplete");
  var c=js(root+"/BATCH_CONTRACT.json"),row=null;for(var i=0;i<c.rows.length;i++)if(c.rows[i].row_id===id)row=c.rows[i];if(!row)throw Error("unknown row");
  if(!/^25\.2(?:\.|x131$|$)/.test(String(app.version)))throw Error("AE version "+app.version);
  app.newProject();var pr=app.project;pr.bitsPerChannel=32;pr.workingSpace="";pr.linearBlending=false;pr.gpuAccelType=GpuAccelType.SOFTWARE;
  if(pr.bitsPerChannel!==32||Number(pr.gpuAccelType)!==1816||pr.linearBlending)throw Error("project contract readback");
  var primary=pr.importFile(new ImportOptions(new File(root+"/"+row.source_member))),noise=pr.importFile(new ImportOptions(new File(root+"/"+row.noise_layer_member)));primary.mainSource.alphaMode=AlphaMode.STRAIGHT;noise.mainSource.alphaMode=AlphaMode.STRAIGHT;
  var comp=pr.items.addComp(row.row_id,9,7,1,1,24),noiseLayer=comp.layers.add(noise),layer=comp.layers.add(primary);noiseLayer.enabled=false;
  var effect=layer.property("ADBE Effect Parade").addProperty("OLM RadialBlur");if(!effect||effect.matchName!=="OLM RadialBlur")throw Error("effect identity");
  var writes=[];for(var m in row.parameters)if(row.parameters.hasOwnProperty(m)){var p=one(effect,m),want=row.parameters[m];p.setValue(want);if(!same(val(p.value),want))throw Error("parameter readback "+m);writes.push({match_name:m,value:val(p.value)});}
  var lp=one(effect,row.noise_layer_match_name),written=noiseLayer.index,readback=null;
  try{lp.setValue(written);readback=Number(lp.value);}catch(bindError){throw Error("NOISE_LAYER_BINDING_UNAVAILABLE: "+bindError.toString()+"; propertyValueType="+lp.propertyValueType+"; pre-bound AEP or host API bridge required");}
  if(readback!==written)throw Error("NOISE_LAYER_BINDING_UNAVAILABLE: write/readback mismatch "+written+"/"+readback);
  wr(ready,{nonce:nonce,row_id:id,ae_pid:0,ae_version:String(app.version),renderer_raw:Number(pr.gpuAccelType),depth:Number(pr.bitsPerChannel),noise_layer_written:written,noise_layer_readback:readback,parameters:writes});
  var marker=new File(go),until=(new Date()).getTime()+600000;while(!marker.exists&&(new Date()).getTime()<until)$.sleep(100);if(!marker.exists)throw Error("continue timeout");
  var q=pr.renderQueue.items.add(comp);q.timeSpanStart=0;q.timeSpanDuration=1/24;var om=q.outputModule(1);om.applyTemplate(templ);om.file=new File(out+"/effect_on_[#####].exr");var settings=om.getSettings(GetSettingsFormat.STRING);pr.renderQueue.render();var rendered=new File(out+"/effect_on_00000.exr");if(!rendered.exists)rendered=new File(out+"/effect_on_00024.exr");if(!rendered.exists)throw Error("missing EXR");
  var after=[];for(var j=0;j<writes.length;j++){var pp=one(effect,writes[j].match_name);after.push({match_name:writes[j].match_name,value:val(pp.value)});}if(enc(writes)!==enc(after))throw Error("parameter drift");if(Number(lp.value)!==written)throw Error("Noise Layer drift");
  summary={status:"ok",row_id:id,ae_version:String(app.version),renderer_raw:Number(pr.gpuAccelType),depth:Number(pr.bitsPerChannel),noise_layer_written:written,noise_layer_readback:Number(lp.value),noise_layer_source_name:String(noise.name),parameters_before:writes,parameters_after:after,output_source:rendered.fsName,output_settings:settings};
 }catch(e){summary={status:"error",error:e.toString()};}
 wr(result,summary);try{if(app.project)app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES);}catch(_){}try{app.quit();}catch(_){}
}());
