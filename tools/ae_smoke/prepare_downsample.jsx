/* Default-parameter projects and independent no-effect I/O controls. */
(function () {
    function json(v) {
        if(v===null || v===undefined) return 'null';
        if(typeof v==='number' || typeof v==='boolean')return String(v);
        if(typeof v==='string')return '"'+v.replace(/\\/g,'\\\\').replace(/"/g,'\\"').replace(/\r/g,'\\r').replace(/\n/g,'\\n').replace(/\t/g,'\\t')+'"';
        var a=[],k;if(v instanceof Array){for(k=0;k<v.length;k++)a.push(json(v[k]));return '['+a.join(',')+']';}
        for(k in v)if(v.hasOwnProperty(k))a.push(json(k)+':'+json(v[k]));return '{'+a.join(',')+'}';
    }
    function write() {var f=new File(A01.output);f.encoding='UTF-8';if(!f.open('w'))throw Error(f.error);f.write(json(result));f.close();}
    var result={phase:'entered',version:app.version,projects:[]};write();
    try {
        for(var d=0;d<A01.inputs.length;d++) {
            if(app.project)app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES);
            var spec=A01.inputs[d], footage=null, usesTemplate=/\.exr$/i.test(spec.path);
            if(usesTemplate){
                app.open(new File(A01.inputTemplate));
                for(var ti=1;ti<=app.project.numItems;ti++){
                    var candidate=app.project.item(ti);
                    if(candidate.name==='OLM_COLOR_PROBE_INPUT'){
                        if(footage)throw Error('Duplicate template footage');
                        footage=candidate;
                    }
                }
                if(!footage)throw Error('Missing Preserve RGB template footage');
                while(app.project.renderQueue.numItems)app.project.renderQueue.item(app.project.renderQueue.numItems).remove();
                footage.replace(new File(spec.path));
            }else{app.newProject();}
            var pr=app.project;
            pr.bitsPerChannel=spec.depth;pr.workingSpace='';pr.linearBlending=false;pr.linearizeWorkingSpace=false;pr.gpuAccelType=GpuAccelType.SOFTWARE;
            if(!footage)footage=pr.importFile(new ImportOptions(new File(spec.path)));
            // Corpus bytes are already raw PF-world samples: avoid multiplying RGB again.
            if(spec.alphaInterpretation=='premultiplied-black'){
                footage.mainSource.alphaMode=AlphaMode.PREMULTIPLIED;
                footage.mainSource.premulColor=[0,0,0];
            }else{footage.mainSource.alphaMode=AlphaMode.STRAIGHT;}
            var row={depth:pr.bitsPerChannel,workingSpace:pr.workingSpace,linearBlending:pr.linearBlending,linearizeWorkingSpace:pr.linearizeWorkingSpace,gpuAccelType:Number(pr.gpuAccelType),items:[]};
            row.inputInterpretation={method:usesTemplate?'hash-bound Preserve RGB footage replacement':'import',templateSha256:usesTemplate?A01.inputTemplateSha256:null,alphaMode:Number(footage.mainSource.alphaMode),premulColor:footage.mainSource.premulColor};
            for(var divisor=1;divisor<=(spec.corpus?1:4);divisor++) {
            for(var n=-1;n<A01.plugins.length;n++) {
                var name=n<0?'control':A01.plugins[n].plugin;
                if(n>=0 && spec.plugin && name!=spec.plugin)continue;
                var cw=Math.max(4,spec.width),ch=Math.max(4,spec.height);
                var c=pr.items.addComp(name,cw,ch,1,1/24,24),layer=c.layers.add(footage);
                layer.property('ADBE Transform Group').property('ADBE Position').setValue([spec.width/2,spec.height/2]);
                var item={plugin:name,width:spec.width,height:spec.height,depth:spec.depth,divisor:divisor,compWidth:cw,compHeight:ch};
                if(n>=0){var effect=layer.property('ADBE Effect Parade').addProperty(A01.plugins[n].matchName);item.enabled=effect.enabled;item.properties=[];
                    if(spec.parameters)for(var ci=0;ci<spec.parameters.length;ci++){
                        var cp=spec.parameters[ci],cv=cp.value;
                        if(cp.kind=='c')cv=[cv[1]/255,cv[2]/255,cv[3]/255,cv[0]/255];
                        effect.property(cp.slot).setValue(cv);
                    }
                    if(spec.corpus){item.corpus=spec.corpus;item.corpus_sha256=spec.corpus_sha256;}

                    for(var pi=1;pi<=effect.numProperties;pi++) {
                        var prop=effect.property(pi),pd={index:pi,name:prop.name};
                        try{pd.value=prop.value;if(prop.hasMin)pd.min=prop.minValue;if(prop.hasMax)pd.max=prop.maxValue;}catch(pe){}
                        item.properties.push(pd);
                    }}
                var q=pr.renderQueue.items.add(c);
                q.setSettings({'Resolution':['Full','Half','Third','Quarter'][divisor-1]});
                item.renderSettings=q.getSettings(GetSettingsFormat.STRING);item.queueIndex=pr.renderQueue.numItems;q.timeSpanStart=0;q.timeSpanDuration=1/24;
                var om=q.outputModule(1);
                om.applyTemplate(spec.outputTemplate||(spec.depth==8?'TIFF シーケンス (アルファ付き)':'OLM EXR 32 Float'));
                item.outputExtension=spec.outputExtension||(spec.depth==8?'tif':'exr');
                if(cw!=spec.width || ch!=spec.height){
                    if(divisor!=1)throw Error('Tiny corpus requires Full resolution');
                    om.setSettings({'Crop':true,'Crop Top':0,'Crop Left':0,'Crop Right':cw-spec.width,'Crop Bottom':ch-spec.height});
                    om=q.outputModule(1);
                }
                // AE 26.3 exposes Color/Depth as read-only; retain template readback.
                // Decoding and independent controls determine actual output fidelity.
                item.outputPrefix=name+(spec.identity?'-'+spec.identity:'')+'-'+spec.width+'x'+spec.height+'-'+spec.depth+'-d'+divisor;
                om.file=new File(A01.directory+'/'+item.outputPrefix+'_[#####].'+item.outputExtension);
                item.outputSettings=om.getSettings(GetSettingsFormat.STRING);
                if(spec.requireStraight && item.outputSettings.Color!='Straight (Unmatted)')throw Error('Straight alpha readback failed: '+item.outputSettings.Color);
                row.items.push(item);
            }
            }
            row.input=spec;
            row.path=A01.directory+'/'+(spec.identity||'defaults')+'-'+spec.width+'x'+spec.height+'-'+spec.depth+'.aep';pr.save(new File(row.path));
            result.projects.push(row);write();
        }
        result.phase='complete';
    }catch(err){result.phase='error';result.error=String(err);}
    write();
    if(app.project)app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES);
    app.quit();
}());
