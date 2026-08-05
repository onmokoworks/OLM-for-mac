(function(){
var TRACE="/tmp/olm_dblur_host_loader_trace.log";
var PAYLOAD="/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/olmdirectionalblur_mac_ae_software_host_phase_payload_20260805.jsx";
function L(s){var f=new File(TRACE);f.encoding="UTF-8";if(f.open("a")){f.write(String(s)+"\n");f.close()}}
L("loader entered");
try{
var result=$.evalFile(new File(PAYLOAD));
if(result instanceof Error)L("payload returned Error "+result.toString()+" line="+String(result.line)+" file="+String(result.fileName));
else L("payload returned "+String(result));
}catch(e){L("payload exception "+e.toString()+" line="+String(e.line)+" file="+String(e.fileName))}
L("loader exited");
}());
