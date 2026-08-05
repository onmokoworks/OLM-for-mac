// Evaluated only through the fail-observable ES3 loader.
(function () {
    var ROOT = "/Users/onmk/Documents/Projects/Personal/OLM as";
    var OUTPUT = "/tmp/olm_dblur_host_20260805";
    var BINARY = "/Users/onmk/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMDirectionalBlur.plugin/Contents/MacOS/OLMDirectionalBlur";
    var EXPECTED_BINARY = "6a89dd4d9bca3f5b3c7af7782627d1b7b7bb6b0c45afe83945d056f1db7519f0";
    var INPUT_REL = "refs/mac_validation_runs/olmdirectionalblur_8bpc_20260805_run5/input/case_0001_before_effects_fullres_nearest.png";
    var EXPECTED_INPUT = "f11febc8e88b755fbd0b5abe6cb1f427458bc3f8b39419f54f57a0a13b720074";
    var EXPECTED_CONTROL = "cc1bf1aa128dea6197405ee722c66198fb5fcbc213bf2569c7af9f30be4fa4f4";
    var EXPECTED_EFFECT = "91b2af26cfad17c1d0cb620ed9844ceb5254090567350c312c1999d9993a0e05";
    var PARAMS = {"OLM Directional Blur-0001":0,"OLM Directional Blur-0002":1,"OLM Directional Blur-0003":92,"OLM Directional Blur-0005":1690,"OLM Directional Blur-0006":0,"OLM Directional Blur-0007":45,"OLM Directional Blur-0010":0,"OLM Directional Blur-0011":0,"OLM Directional Blur-0012":0,"OLM Directional Blur-0015":0,"OLM Directional Blur-0016":1,"OLM Directional Blur-0017":0,"OLM Directional Blur-0018":1,"OLM Directional Blur-0019":0,"OLM Directional Blur-0020":10};
    function F(m){throw new Error("FAIL_CLOSED: "+m)}
    function Q(v){var q=String.fromCharCode(39);return q+String(v).split(q).join(q+String.fromCharCode(92)+q+q)+q}
    function H(p){var m=system.callSystem("/usr/bin/shasum -a 256 "+Q(p)).match(/^([0-9a-f]{64})/i);if(!m)F("hash "+p);return m[1].toLowerCase()}
    function J(v){return "\""+String(v).replace(/\\/g,"\\\\").replace(/\"/g,"\\\"").replace(/\r/g,"\\r").replace(/\n/g,"\\n")+"\""}
    function W(p,text){var f=new File(p);f.encoding="UTF-8";if(!f.open("w"))F("write "+p);f.write(text+"\n");f.close()}
    function L(text){var f=new File(OUTPUT+"/host_trace.log");f.encoding="UTF-8";if(!f.open("a")){f=new File("/tmp/olm_dblur_host_fallback_trace.log");f.encoding="UTF-8";if(!f.open("a"))return}f.write(String(text)+"\n");f.close()}
    function Find(g,n){for(var i=1;i<=g.numProperties;i++){var p=g.property(i);if(p.matchName===n)return p;if(p.numProperties){var x=Find(p,n);if(x)return x}}return null}
    function Render(comp,e,on,path){e.enabled=on;var f=new File(path);if(f.exists&&!f.remove())F("stale output");comp.saveFrameToPng(0,f);for(var i=0;i<1800&&!f.exists;i++){$.sleep(100);f=new File(f.fsName)}if(!f.exists)F("render missing");return H(f.fsName)}
    try {
    if(!ROOT||!OUTPUT)F("paths");
    var out=new Folder(OUTPUT);if(!out.exists&&!out.create()){L("ERROR output directory");F("output directory")}
    L("start");
    var binary=new File(BINARY);if(!binary.exists||H(BINARY)!==EXPECTED_BINARY)F("installed binary identity");
    L("binary exact");
    var pids=["31792"],processName=system.callSystem("/bin/ps -p 31792 -o comm=");if(processName.indexOf("Adobe After Effects 2026.app/Contents/MacOS/After Effects")<0)F("pinned AE PID required");
    var input=new File(ROOT+"/"+INPUT_REL);if(!input.exists||H(input.fsName)!==EXPECTED_INPUT)F("input identity");
    if(app.project){try{app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES)}catch(closeError){F("close previous project "+closeError)}}
    var project=app.newProject();if(!project)project=app.project;if(!project)F("new project");project.bitsPerChannel=8;project.linearBlending=false;try{project.gpuAccelType=GpuAccelType.SOFTWARE}catch(e){F("SOFTWARE renderer "+e)}
    if(Number(project.bitsPerChannel)!==8||Number(project.gpuAccelType)!==1816||(String(project.workingSpace)!==""&&String(project.workingSpace)!=="None"))F("project contract");
    var footage=project.importFile(new ImportOptions(input));var comp=project.items.addComp("case_0001",1920,1080,1,1,24);comp.resolutionFactor=[2,2];if(comp.resolutionFactor[0]!==2||comp.resolutionFactor[1]!==2)F("resolution factor");L("render dimensions 960x540 from 1920x1080 factor 2x2");
    var layer=comp.layers.add(footage);var effect=layer.property("ADBE Effect Parade").addProperty("OLM Directional Blur");if(!effect||effect.matchName!=="OLM Directional Blur")F("effect identity");
    L("effect exact; module mapping requires external pre/post attestation");
    for(var key in PARAMS){if(PARAMS.hasOwnProperty(key)){var p=Find(effect,key);if(!p)F("parameter "+key);p.setValue(PARAMS[key])}}
    var projectFile=new File(out.fsName+"/olmdirectionalblur_pf8_host_fixture.aep");if(projectFile.exists)F("stale project");project.save(projectFile);if(!projectFile.exists)F("project save");
    var control=Render(comp,effect,false,out.fsName+"/case_0001__no_effect.png");if(control!==EXPECTED_CONTROL)F("control output "+control);
    var actual=Render(comp,effect,true,out.fsName+"/case_0001__effect_on.png");if(actual!==EXPECTED_EFFECT)F("actual output "+actual);
    if(H(binary.fsName)!==EXPECTED_BINARY)F("post-render binary identity");
    W(out.fsName+"/result.json","{\"status\":\"pass\",\"plugin\":\"OLMDirectionalBlur\",\"binary_sha256\":\""+EXPECTED_BINARY+"\",\"loaded_path\":"+J(BINARY)+",\"ae_pid\":"+Number(pids[0])+",\"bits_per_channel\":8,\"renderer\":\"SOFTWARE\",\"project_sha256\":\""+H(projectFile.fsName)+"\",\"control_sha256\":\""+control+"\",\"actual_output_sha256\":\""+actual+"\"}");
    L("PASS output="+actual);
    try { project.close(CloseOptions.DO_NOT_SAVE_CHANGES); } catch(e) {}
    }catch(runError){L("ERROR "+runError.toString()+" line="+String(runError.line))}
}());
