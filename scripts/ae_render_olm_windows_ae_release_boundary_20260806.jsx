/* Render one BATCH_CONTRACT.json row. Launched only by the companion PS1. */
(function () {
    function env(name) { try { return $.getenv(name) || ""; } catch (_) { return ""; } }
    function read(path) { var f = new File(path); f.encoding = "UTF-8"; if (!f.open("r")) throw new Error("open: " + path); var s=f.read(); f.close(); return s; }
    function json(path) { return eval("(" + read(path) + ")"); }
    function write(path, value) { var f=new File(path); f.encoding="UTF-8"; if(!f.open("w")) throw new Error("write: "+path); f.write(value); f.close(); }
    function esc(s) { return String(s).replace(/\\/g,"\\\\").replace(/"/g,'\\"').replace(/\r/g,"\\r").replace(/\n/g,"\\n"); }
    function encode(v) {
        if (v === null) return "null";
        if (typeof v === "boolean" || typeof v === "number") return String(v);
        if (typeof v === "string") return '"' + esc(v) + '"';
        if (Object.prototype.toString.call(v) === "[object Array]") { var a=[]; for(var i=0;i<v.length;i++) a.push(encode(v[i])); return "["+a.join(",")+"]"; }
        var p=[]; for(var k in v) if(v.hasOwnProperty(k)) p.push('"'+esc(k)+'":'+encode(v[k])); return "{"+p.join(",")+"}";
    }
    function die(message) { throw new Error(message); }
    function findItems(project, name) { var a=[]; for(var i=1;i<=project.numItems;i++) if(project.item(i).name===name) a.push(project.item(i)); return a; }
    function leaves(group, matchName, out) {
        if (!group || !group.numProperties) return;
        for(var i=1;i<=group.numProperties;i++) { var p=group.property(i); if(p.matchName===matchName) out.push(p); if(p.numProperties) leaves(p,matchName,out); }
    }
    function value(v) { if(Object.prototype.toString.call(v)==="[object Array]"){var a=[];for(var i=0;i<v.length;i++)a.push(v[i]);return a;}return v; }
    function same(a,b,mode) {
        if(mode==="float32_u32_vector") {
            if(Object.prototype.toString.call(a)!=="[object Array]"||Object.prototype.toString.call(b)!=="[object Array]"||a.length!==b.length)return false;
            for(var i=0;i<a.length;i++) if(Math.abs(Number(a[i])-Number(b[i]))>0.00000012)return false;
            return true;
        }
        return Number(a)===Number(b);
    }
    function resolve(effect, spec) {
        var found=[]; leaves(effect,spec.match_name,found);
        if(found.length!==1) die("property cardinality " + spec.match_name + " = " + found.length);
        var p=found[0];
        if(spec.property_index!==undefined && Number(p.propertyIndex)!==Number(spec.property_index)) die("property_index " + spec.match_name);
        if(spec.display_name!==undefined && String(p.name)!==String(spec.display_name)) die("display_name " + spec.match_name);
        if(spec.property_type!==undefined && Number(p.propertyValueType)!==Number(spec.property_type)) die("property_type " + spec.match_name + " actual="+p.propertyValueType);
        return p;
    }
    function snapshot(effect,writes) { var a=[]; for(var i=0;i<writes.length;i++){var p=resolve(effect,writes[i]); a.push({match_name:p.matchName,display_name:p.name,property_index:Number(p.propertyIndex),property_type:Number(p.propertyValueType),value:value(p.value)});} return a; }
    function render(comp,effect,enabled,path,template,start,duration) {
        effect.enabled=enabled;
        var q=app.project.renderQueue.items.add(comp); q.timeSpanStart=start; q.timeSpanDuration=duration;
        if(Number(q.timeSpanStart)!==Number(start)||Number(q.timeSpanDuration)!==Number(duration)) die("render queue time readback");
        var om=q.outputModule(1); om.applyTemplate(template); om.file=new File(path.replace(/\.exr$/i,"_[#####].exr"));
        var settings=om.getSettings(GetSettingsFormat.STRING); app.project.renderQueue.render();
        var expected=new File(path.replace(/\.exr$/i,"_00024.exr"));
        if(!expected.exists) { expected=new File(path.replace(/\.exr$/i,"_00000.exr")); }
        if(!expected.exists) die("missing rendered EXR for " + path);
        q.remove(); return {path:expected.fsName,settings:settings};
    }
    var root=env("OLM_BOUNDARY_ROOT"), rowId=env("OLM_BOUNDARY_ROW_ID"), out=env("OLM_BOUNDARY_ROW_OUTPUT"), result=env("OLM_BOUNDARY_RESULT"), ready=env("OLM_BOUNDARY_READY"), go=env("OLM_BOUNDARY_CONTINUE"), nonce=env("OLM_BOUNDARY_NONCE"), template=env("OLM_BOUNDARY_OUTPUT_TEMPLATE");
    var summary={status:"error",error:""};
    try {
        if(!root||!rowId||!out||!result||!ready||!go||!nonce||!template) die("runner environment incomplete");
        var contract=json(root+"/BATCH_CONTRACT.json"), row=null;
        for(var ri=0;ri<contract.acquire.length;ri++) if(contract.acquire[ri].row_id===rowId) row=contract.acquire[ri];
        if(!row) die("unknown row_id");
        var pr=app.open(new File(root+"/"+row.project_contract.input_interpretation.template_member));
        if(!/^26\.3(?:\.|$)/.test(String(app.version))) die("AE version " + app.version);
        pr.bitsPerChannel=Number(row.depth); pr.workingSpace=""; pr.linearBlending=false; pr.gpuAccelType=GpuAccelType.SOFTWARE;
        if(Number(pr.bitsPerChannel)!==Number(row.depth)||Number(pr.gpuAccelType)!==1816||pr.linearBlending) die("project contract readback");
        var ii=row.project_contract.input_interpretation, footage=findItems(pr,ii.footage_item_name), comps=findItems(pr,ii.comp_item_name);
        if(footage.length!==1||comps.length!==1) die("template item cardinality");
        footage[0].replace(new File(root+"/"+row.source_member)); footage[0].mainSource.alphaMode=AlphaMode.STRAIGHT;
        var comp=comps[0]; comp.width=Number(row.comp.width); comp.height=Number(row.comp.height); comp.pixelAspect=Number(row.comp.pixel_aspect); comp.frameRate=Number(row.comp.frame_rate); comp.duration=Number(row.comp.duration_seconds);
        var layer=comp.layer(Number(ii.comp_layer_index));
        if(comp.numLayers!==Number(ii.expected_num_layers)||layer.source.id!==footage[0].id) die("source replacement binding");
        var cs=row.comp; if(comp.width!==cs.width||comp.height!==cs.height||Number(comp.frameRate)!==Number(cs.frame_rate)||Number(comp.pixelAspect)!==Number(cs.pixel_aspect)) die("comp contract");
        layer.startTime=cs.source_layer_timing.startTime; layer.inPoint=cs.source_layer_timing.inPoint; layer.outPoint=cs.source_layer_timing.outPoint; layer.stretch=cs.source_layer_timing.stretch; layer.scale.setValue(cs.source_layer_scale);
        var parade=layer.property("ADBE Effect Parade"); if(parade.numProperties!==0) die("template effect contamination");
        var effect=parade.addProperty(row.effect.match_name); if(!effect||effect.matchName!==row.effect.match_name||effect.name!==row.effect.display_name) die("effect identity");
        for(var wi=0;wi<row.parameter_writes.length;wi++){var w=row.parameter_writes[wi],p=resolve(effect,w);p.setValue(value(w.value));if(!same(value(p.value),value(w.value),w.comparison_mode)) die("parameter write readback " + w.match_name);}
        for(var si=0;si<row.standard_options.length;si++){var sw=row.standard_options[si],sp=resolve(effect,sw);sp.setValue(value(sw.value));if(!same(value(sp.value),value(sw.value),sw.comparison_mode)) die("standard option readback " + sw.match_name);}
        var before=snapshot(effect,row.parameter_writes);
        var pid=system.callSystem('powershell.exe -NoProfile -NonInteractive -Command "$id=$PID;for($i=0;$i -lt 8;$i++){$p=Get-CimInstance Win32_Process -Filter (\'ProcessId=\'+$id);if(!$p){break};if($p.Name -ieq \'AfterFX.exe\'){$p.ProcessId;break};$id=$p.ParentProcessId}"').replace(/\s/g,"");
        if(!/^\d+$/.test(pid)) die("AfterFX PID binding");
        write(ready,encode({nonce:nonce,row_id:rowId,ae_pid:Number(pid),ae_version:String(app.version),renderer_raw:Number(pr.gpuAccelType),bits_per_channel:Number(pr.bitsPerChannel),working_space_raw:String(pr.workingSpace),linear_blending:pr.linearBlending,parameters_before:before})+"\n");
        var marker=new File(go),deadline=(new Date()).getTime()+600000; while(!marker.exists&&(new Date()).getTime()<deadline) $.sleep(100); if(!marker.exists) die("continue timeout");
        var no=render(comp,effect,false,out+"/no_effect.exr",template,cs.render_time_span_start_seconds,cs.render_time_span_duration_seconds);
        var yes=render(comp,effect,true,out+"/effect_on.exr",template,cs.render_time_span_start_seconds,cs.render_time_span_duration_seconds);
        var after=snapshot(effect,row.parameter_writes); if(encode(before)!==encode(after)) die("parameter readback drift");
        summary={status:"ok",row_id:rowId,ae_pid:Number(pid),ae_version:String(app.version),renderer_raw:Number(pr.gpuAccelType),bits_per_channel:Number(pr.bitsPerChannel),working_space_raw:String(pr.workingSpace),linear_blending:pr.linearBlending,parameters_before:before,parameters_after:after,no_effect_source:no.path,effect_on_source:yes.path,no_effect_settings:no.settings,effect_on_settings:yes.settings};
    } catch(e) { summary={status:"error",error:e.toString()}; }
    write(result,encode(summary)+"\n");
    try { if(app.project) app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES); } catch(_) {}
    try { app.quit(); } catch(_) {}
}());
