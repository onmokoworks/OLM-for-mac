import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import autoport as a
import vectors as v
from make_demo import demos


class AutoportTests(unittest.TestCase):
    def test_diamond_is_leaf_first(self):
        order, blocked = a.leaf_order({"root","a","b","leaf"},[("root","a"),("root","b"),("a","leaf"),("b","leaf")])
        self.assertEqual(order,["leaf","a","b","root"])
        self.assertEqual(blocked,[])

    def test_cycle_blocks_ancestors_but_not_independent_leaf(self):
        order, blocked = a.leaf_order({"r","a","b","ok"},[("r","a"),("a","b"),("b","a")])
        self.assertEqual(order,["ok"])
        self.assertEqual(blocked,["a","b","r"])

    def test_self_recursion_is_not_a_leaf(self):
        self.assertEqual(a.leaf_order({"r"},[("r","r")]),([],["r"]))

    def test_prompt_does_not_leak_imported_reference_comments(self):
        node={"address":"123456","c":"/* secret Rust mapping */ int f(){return 1;}","signature":"int f()"}
        text=a.prompt_for(node,{"rust_signature":"fn x()"},{},[],"no-fma")
        self.assertNotIn("secret Rust mapping",text)
        self.assertIn("Mode::NoFma",text)
        self.assertIn("return 1",text)

    def test_reject_std_math_and_linked_reference(self):
        prefix='pub unsafe extern "C" fn autoport_123456() {}\n'
        for bad in ['fn f(x:f32){ x.sin(); }','#[link(name="original")] extern "C" {}','include!("answer.rs");']:
            with self.assertRaises(ValueError):
                a.validate_source(prefix+bad,"autoport_123456")
        a.validate_source(prefix,"autoport_123456")

    def test_numeric_edges_are_bits(self):
        rows=list(v.scalar_vectors({"args":["f32","f64"],"return":"f32"},1))
        bits={r["args"][0]["bits"] for r in rows}
        self.assertTrue({"0x80000000","0x1","0x7f800000","0x7fc01234"} <= bits)
        json.dumps(rows,allow_nan=False)

    def test_pointer_without_contract_refused(self):
        with self.assertRaises(ValueError):
            list(v.scalar_vectors({"args":["ptr"],"return":"void"},0))

    def test_scalar_inference_refuses_unknown_abi_and_global_state(self):
        inferred=a.infer_scalar_contract({"address":"123456","c":"float f(float x) { return x * 2.0; }"})
        self.assertEqual(inferred["abi"],{"args":["f32"],"return":"f32"})
        for c in ["undefined8 f(void) {return 0;}","int f(int *p) {return *p;}","int f(void) {return DAT_123456;}"]:
            self.assertIsNone(a.infer_scalar_contract({"address":"123456","c":c}))

    def test_pack_preserves_alias_and_guards(self):
        rows=[{"label":"alias","buffers":{"b":{"size":8,"fill":7}},
               "args":[v.ptr("b"),v.ptr("b",1)],"return":"void"}]*2
        spec=v.pack(rows,"original.aex",16,"fma")
        first,second=spec["calls"]
        self.assertEqual(first["args"][1]["offset"]-first["args"][0]["offset"],1)
        self.assertGreater(second["args"][0]["offset"],first["args"][0]["offset"]+8)
        data=bytes.fromhex(spec["buffers"]["arena"]["hex"])
        self.assertEqual(data[:16],bytes([0xd3])*16)

    def test_demo_corpora_have_no_expected_outputs(self):
        for config in demos(Path("originals")).values():
            for contract in config["contracts"].values():
                rows=v.generate(contract,20261112)
                self.assertGreaterEqual(len(rows),64)
                self.assertFalse(any("expected" in r for r in rows))
                spec=v.pack(rows,"original.aex",0x1000,"fma")
                self.assertEqual(len(spec["calls"]),len(rows))

    def test_empty_corpus_and_wrong_abi_fail(self):
        with self.assertRaises(ValueError):
            v.generate({"fixture":"recorded","abi":{"args":[],"return":"void"}},1)
        with self.assertRaises(ValueError):
            v.generate({"fixture":"copy8","abi":{"args":[],"return":"void"}},1)

    def test_comparison_checks_bits_and_completeness(self):
        with tempfile.TemporaryDirectory() as tmp:
            dirs=[Path(tmp)/s for s in ["a","b"]]
            spec={"calls":[{}],"buffers":{"arena":{"size":4}}}
            for d in dirs:
                d.mkdir()
                a.write(d/"result.json",{"calls":[{"index":0,"return":{"bits_le":""},"buffers":{"arena":"data.bin"}}]})
            (dirs[0]/"data.bin").write_bytes(bytes(4))
            (dirs[1]/"data.bin").write_bytes(bytes.fromhex("00000080"))
            self.assertEqual(a.compare_witness(*dirs,spec)["offset"],3)  # +0 != -0
            (dirs[1]/"data.bin").write_bytes(bytes(4))
            self.assertIsNone(a.compare_witness(*dirs,spec))
            a.write(dirs[1]/"result.json",{"calls":[]})
            with self.assertRaises(ValueError):
                a.compare_witness(*dirs,spec)

    def test_aslr_pointer_offsets_are_compared_not_masked(self):
        with tempfile.TemporaryDirectory() as tmp:
            dirs=[Path(tmp)/s for s in ["a","b"]]
            spec={"calls":[{}],"buffers":{"arena":{"size":16,"pointers":[{"offset":0},{"offset":8}]}}}
            for d,base in zip(dirs,[0x100000,0x200000]):
                d.mkdir()
                a.write(d/"result.json",{"calls":[{"index":0,"return":{"bits_le":""},"buffers":{"arena":"data.bin"}}]})
                (d/"data.bin").write_bytes((base+4).to_bytes(8,"little")+base.to_bytes(8,"little"))
            self.assertIsNone(a.compare_witness(*dirs,spec))
            (dirs[1]/"data.bin").write_bytes((0x200008).to_bytes(8,"little")+(0x200000).to_bytes(8,"little"))
            self.assertIsNotNone(a.compare_witness(*dirs,spec))

    def test_graph_budget_keeps_missing_external_endpoint(self):
        class Hub:
            def programs_list(self): return [{"name":"p","sha256":"hash"}]
            def call_graph(self,**kwargs): return {"nodes":[{"address":"123456"}],"edges":[["123456","EXTERNAL:1"]]}
            def decompile_batch(self,**kwargs): return {"results":[{"address":"123456","completed":True,"c":"int f(){return 0;}"}]}
        class PE:
            OPTIONAL_HEADER=type("Header",(),{"ImageBase":0x100000})()
            def __enter__(self): return self
            def __exit__(self,*args): pass
        with tempfile.TemporaryDirectory() as tmp, patch.object(a,"hub",return_value=Hub()), patch.object(a,"digest",return_value="hash"), patch("pefile.PE",return_value=PE()):
            result=a.export({"hub":"local","program":"p","aex":"original","roots":["123456"],"max_nodes":1},Path(tmp))
            self.assertEqual(len(result["nodes"]),1)
            self.assertEqual(result["frontier"],["EXTERNAL:1"])

    def test_completed_graph_integration_still_requires_oracle(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/"work/src").mkdir(parents=True)
            source=root/"adapter.rs"
            source.write_text("// reviewed adapter")
            config={"integration":{"files":{"src/algorithm.rs":{"path":str(source),"sha256":a.digest(source)}}},
                    "indirect_reviewed":True,"crate_name":"fixture","aex":"original","oracle_seconds":5}
            state={"functions":{"123456":{"status":"verified"}}}
            graph={"nodes":{"123456":{}},"frontier":[]}
            with patch.object(a,"run",return_value={"returncode":1,"timeout":False}):
                a.final_oracle(config,root,state,graph)
            self.assertEqual(state["integration"],"wired")
            self.assertEqual(state["status"],"needs_human")
            self.assertEqual((root/"work/src/algorithm.rs").read_text(),source.read_text())

    def test_known_function_cannot_be_matched_by_name_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"exchange.json"
            a.write(p,{"functions":[{"verified":True,"name":"same","original_sha256":"wrong"}]})
            found,_=a.known_lookup({"known_functions":str(p)},{"identity":{"sha256":"right"},"nodes":{}})
            self.assertEqual(found,{})

    def controller_fixture(self, root):
        original=root/"original.aex"
        original.write_bytes(b"fixture-original")
        config={"aex":str(original),"codex":"fake-codex","contracts":{"123456":{
            "abi":{"args":[],"return":"u32"},"fixture":"scalar",
            "rust_signature":'pub unsafe extern "C" fn autoport_123456() -> u32'}},
            "max_functions":1,"attempts":2,"function_seconds":10,"attempt_seconds":5,
            "generation_seconds":4,"seed":1,"fma":"fma","effort":"low",
            "crate_name":"fixture","program":"fixture","annotate":False,"oracle":False}
        (root/"work/src/autoport").mkdir(parents=True)
        graph={"nodes":{"123456":{"address":"123456","completed":True,"c":"int f(){return 1;}"}},
               "edges":[],"imports":[],"frontier":[]}
        a.write(root/"graph.json",graph)
        state={"run_id":"test","config_hash":a.fingerprint(config),"original_sha256":a.digest(original),
               "order":["123456"],"cycles_and_dependents":[],"functions":{
                   "123456":{"status":"pending","attempts":[],"seconds":0}}}
        a.write(root/"state.json",state)
        return config,state

    @staticmethod
    def fake_run(argv,out,timeout,**kwargs):
        out.mkdir(parents=True)
        (out/"stdout.txt").write_text("")
        if argv[0] == "fake-codex":
            a.write(out.parent/"answer.json",{"code":'#[no_mangle] pub unsafe extern "C" fn autoport_123456() -> u32 {1}',"notes":""})
        return {"returncode":0,"timeout":False,"seconds":0.001}

    def test_mismatch_feedback_retry_and_resume_without_regeneration(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            config,_=self.controller_fixture(root)
            with patch.object(a,"run",side_effect=self.fake_run) as runner, patch.object(a,"verify",side_effect=[
                {"exact":False,"minimal_vector":{"label":"failure"}}, {"exact":True}]) as verifier:
                self.assertEqual(a._execute(config,root),2)  # function exact != render complete
                self.assertEqual(verifier.call_count,2)
                self.assertEqual(runner.call_count,4)
            state=a.read(root/"state.json")
            self.assertEqual(state["functions"]["123456"]["status"],"verified")
            prompt=(root/"functions/123456/attempt-02/prompt.txt").read_text()
            self.assertIn('"label": "failure"',prompt)
            with patch.object(a,"run",side_effect=AssertionError("must not regenerate")):
                a._execute(config,root)

    def test_interrupted_attempt_consumes_budget_on_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            config,state=self.controller_fixture(root)
            state["functions"]["123456"].update(status="translating",attempts=[{
                "status":"running","reserved_seconds":10}])
            a.write(root/"state.json",state)
            with patch.object(a,"run",side_effect=AssertionError("budget exhausted")):
                a._execute(config,root)
            row=a.read(root/"state.json")["functions"]["123456"]
            self.assertEqual(row["status"],"needs_human")
            self.assertEqual(row["seconds"],10)

    def test_resume_refuses_original_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            config,_=self.controller_fixture(root)
            Path(config["aex"]).write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError,"drift"):
                a._execute(config,root)


if __name__ == "__main__":
    unittest.main()
