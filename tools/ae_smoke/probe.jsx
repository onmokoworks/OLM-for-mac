/* A01 registration/parameter probe. No rendering or exactness claim. */
(function () {
    function json(v) {
        if (v === null || v === undefined) return 'null';
        if (typeof v === 'number') return isFinite(v) ? String(v) : 'null';
        if (typeof v === 'boolean') return String(v);
        if (typeof v === 'string') return '"' + v.replace(/\\/g,'\\\\').replace(/"/g,'\\"').replace(/\r/g,'\\r').replace(/\n/g,'\\n').replace(/\t/g,'\\t') + '"';
        var a=[], k;
        if (v instanceof Array) { for(k=0;k<v.length;k++) a.push(json(v[k])); return '['+a.join(',')+']'; }
        for(k in v) if(v.hasOwnProperty(k)) a.push(json(k)+':'+json(v[k]));
        return '{'+a.join(',')+'}';
    }
    function write(v) {
        var f=new File(A01.output); f.encoding='UTF-8';
        if(!f.open('w')) throw new Error('Cannot write probe output: '+f.error);
        f.write(json(v)); f.close();
    }
    function param(p) {
        var r={index:p.propertyIndex,name:p.name,matchName:p.matchName,type:String(p.propertyType)};
        if(p.propertyType === PropertyType.PROPERTY) {
            r.valueType=String(p.propertyValueType);
            try {r.defaultValue=p.value;} catch(e) {r.valueError=String(e);}
            try {if(p.hasMin) r.min=p.minValue; if(p.hasMax) r.max=p.maxValue;} catch(e) {}
            r.popupItems=null; // ExtendScript exposes no third-party popup label getter.
        } else {r.children=[]; for(var n=1;n<=p.numProperties;n++) r.children.push(param(p.property(n)));}
        return r;
    }
    var result={version:app.version,phase:'entered',effects:[],rows:[]};
    write(result);
    try {
        var effects=app.effects;
        for(var i=0;i<effects.length;i++) result.effects.push({displayName:effects[i].displayName,matchName:effects[i].matchName,version:effects[i].version});
        app.newProject(); app.project.workingSpace=''; app.project.linearBlending=false;
        app.project.linearizeWorkingSpace=false; app.project.gpuAccelType=GpuAccelType.SOFTWARE;
        for(var j=0;j<A01.plugins.length;j++) {
            var spec=A01.plugins[j], r={plugin:spec.plugin,matchName:spec.matchName,registered:false,applied:false};
            for(var k=0;k<result.effects.length;k++) if(result.effects[k].matchName===spec.matchName) r.registered=true;
            try {
                var c=app.project.items.addComp(spec.plugin,32,24,1,1,24);
                var l=c.layers.addSolid([0.25,0.5,0.75],'probe',32,24,1);
                var e=l.property('ADBE Effect Parade').addProperty(spec.matchName);
                r.applied=!!e; r.params=param(e);
            } catch(err) {r.error=String(err);}
            result.rows.push(r); write(result);
        }
        var q=app.project.renderQueue.items.add(c), om=q.outputModule(1);
        result.templates=[];
        var templates=om.templates;
        for(var t=0;t<templates.length;t++) {
            var tr={name:templates[t]};
            try {om.applyTemplate(templates[t]); tr.settings=om.getSettings(GetSettingsFormat.STRING);} catch(err) {tr.error=String(err);}
            result.templates.push(tr);
        }
        q.remove();
        result.phase='complete';
    } catch(err) {result.phase='error';result.error=String(err);}
    write(result);
    // Driver retains the process briefly for vmmap identity and modal screenshots.
}());
