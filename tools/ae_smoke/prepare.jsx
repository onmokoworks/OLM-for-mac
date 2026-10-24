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
            app.newProject();var pr=app.project, spec=A01.inputs[d];
            pr.bitsPerChannel=spec.depth;pr.workingSpace='';pr.linearBlending=false;pr.linearizeWorkingSpace=false;pr.gpuAccelType=GpuAccelType.SOFTWARE;
            var footage=pr.importFile(new ImportOptions(new File(spec.path)));
            footage.mainSource.alphaMode=AlphaMode.STRAIGHT;
            var row={depth:pr.bitsPerChannel,workingSpace:pr.workingSpace,linearBlending:pr.linearBlending,linearizeWorkingSpace:pr.linearizeWorkingSpace,gpuAccelType:Number(pr.gpuAccelType),items:[]};
            for(var n=-1;n<A01.plugins.length;n++) {
                var name=n<0?'control':A01.plugins[n].plugin;
                var c=pr.items.addComp(name,spec.width,spec.height,1,1/24,24),layer=c.layers.add(footage);
                var item={plugin:name};
                if(n>=0){var effect=layer.property('ADBE Effect Parade').addProperty(A01.plugins[n].matchName);item.enabled=effect.enabled;}
                var q=pr.renderQueue.items.add(c);q.timeSpanStart=0;q.timeSpanDuration=1/24;
                var om=q.outputModule(1);
                om.applyTemplate(spec.depth==32?'OLM EXR 32 Float':'TIFF シーケンス (アルファ付き)');
                om.setSettings({'Color':'Straight (Unmatted)','Depth':spec.depth==32?'Floating Point+':spec.depth==16?'Trillions of Colors+':'Millions of Colors+'});
                om.file=new File(A01.directory+'/'+name+'-'+spec.depth+'_[#####].'+(spec.depth==32?'exr':'tif'));
                item.outputSettings=om.getSettings(GetSettingsFormat.STRING);row.items.push(item);
            }
            row.path=A01.directory+'/defaults-'+spec.depth+'.aep';pr.save(new File(row.path));
            result.projects.push(row);write();
        }
        result.phase='complete';
    }catch(err){result.phase='error';result.error=String(err);}
    write();
}());
