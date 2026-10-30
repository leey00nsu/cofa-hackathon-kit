"""Fictional, isolated automation checks; no real project or rehearsal is read."""
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from http.server import BaseHTTPRequestHandler, HTTPServer
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("auto_kit", ROOT / "scripts/kit.py")
kit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(kit)
NODE = shutil.which("node")


class AutomaticTestingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()

    def tearDown(self):
        self.temp.cleanup()

    def test_node_tap_parser_excludes_skips_todos_and_cancelled_cases(self):
        output = "# tests 4\n# pass 1\n# fail 0\n# cancelled 1\n# skipped 1\n# todo 1\n"
        result = kit.test_summary(["node", "--test"], output, "auto")
        self.assertEqual(result["runner"], "node")
        self.assertEqual(result["effective"], 1)
        self.assertEqual(result["cancelled"], 1)
        self.assertEqual(kit.test_summary(["node", "--test"], "# tests 0\n", "auto")["state"], "UNKNOWN")
        combined = kit.test_summary(["npm", "test"],
            "# tests 1\n# pass 0\n# fail 1\n# skipped 0\n# todo 0\n"
            "# tests 1\n# pass 1\n# fail 0\n# skipped 0\n# todo 0\n", "node")
        self.assertEqual(combined["failed"], 1)
        self.assertEqual(combined["total"], 2)

    @unittest.skipUnless(NODE, "Node unavailable; native runtime behavior not verified")
    def test_real_node_mixed_empty_and_pending_runs(self):
        cases = {
            "mixed": "test('actual fixture',()=>assert.equal(2+3,5)); test.skip('skipped',()=>{}); test.todo('todo');",
            "empty": "",
            "pending": "test.skip('skipped',()=>{}); test.todo('todo');",
        }
        for name, body in cases.items():
            target = self.root / name
            target.mkdir()
            if name != "empty":
                (target / "feature.test.mjs").write_text("import test from 'node:test'; import assert from 'node:assert/strict';\n" + body)
            record = kit.record_check(target, name, [NODE, "--test", "--test-reporter=tap"], 10)
            self.assertEqual(record["result"], "PASS" if name == "mixed" else "NOT_RUN")
            self.assertEqual(record["tests"]["effective"], 1 if name == "mixed" else 0)

    @unittest.skipUnless(NODE, "Node unavailable")
    def test_native_failure_is_retained_and_wrapper_cannot_hide_it(self):
        path = self.root / "bad.test.mjs"
        path.write_text("import test from 'node:test'; import assert from 'node:assert/strict'; test('bad fixture',()=>assert.equal(1,2));")
        failed = kit.record_check(self.root, "failed-node", [NODE, "--test", "--test-reporter=tap", str(path)], 10)
        self.assertEqual(failed["result"], "FAIL")
        self.assertNotEqual(failed["exit_code"], 0)
        # A wrapper returning 0 must not conceal failed native test output.
        wrapper = self.root / "wrapper.mjs"
        wrapper.write_text("import {spawnSync} from 'node:child_process'; const p=spawnSync(process.execPath,['--test','--test-reporter=tap','bad.test.mjs'],{encoding:'utf8'}); process.stdout.write(p.stdout);")
        hidden = kit.record_check(self.root, "wrapped-node", [NODE, str(wrapper)], 10, runner="node")
        self.assertEqual(hidden["exit_code"], 0)
        self.assertEqual(hidden["result"], "FAIL")

    def test_installed_reference_templates_are_not_discoverable_tests(self):
        kit.install(self.root, "none")
        refs = list((self.root / ".hackathon/testing").rglob("*.example"))
        self.assertEqual(len(refs), 4)
        self.assertFalse(list((self.root / ".hackathon/testing").rglob("test_*.py")))
        self.assertFalse(list((self.root / ".hackathon/testing").rglob("*.test.mjs")))

    def python_helpers(self):
        path = ROOT / "templates/testing/python/http_fixture.py.example"
        loader = importlib.machinery.SourceFileLoader("http_fixture", str(path))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)
        return module

    def test_python_fixture_real_http_restart_and_cleanup(self):
        helpers = self.python_helpers()
        sentinel = self.root / "existing-data.txt"
        sentinel.write_text("preserve")
        with helpers.isolated_directory() as state:
            def factory(host, port):
                class Handler(BaseHTTPRequestHandler):
                    def do_POST(self):
                        (state / "value.json").write_bytes(self.rfile.read(int(self.headers["Content-Length"])))
                        self.send_response(201); self.end_headers()
                    def do_GET(self):
                        self.send_response(200); self.end_headers(); self.wfile.write((state / "value.json").read_bytes())
                    def log_message(self, *args):
                        pass
                return HTTPServer((host, port), Handler)
            with helpers.http_server(factory) as client:
                self.assertEqual(client.request("POST", "/", {"value": 7}).status, 201)
                with self.assertRaises(ValueError):
                    client.request("GET", "https://example.invalid/")
            with helpers.http_server(factory) as client:
                self.assertEqual(client.request("GET", "/").json(), {"value": 7})
        self.assertFalse(state.exists())
        self.assertEqual(sentinel.read_text(), "preserve")

    def test_python_fixture_cleans_up_after_test_failure(self):
        helpers = self.python_helpers()
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200); self.end_headers(); self.wfile.write(b"fixture")
            def log_message(self, *args):
                pass
        with self.assertRaisesRegex(RuntimeError, "forced fixture failure"):
            with helpers.isolated_directory() as state:
                with helpers.http_server(lambda host, port: HTTPServer((host, port), Handler)) as client:
                    self.assertEqual(client.request("GET", "/").status, 200)
                    raise RuntimeError("forced fixture failure")
        self.assertFalse(state.exists())
        with self.assertRaises(OSError):
            client.request("GET", "/")

    @unittest.skipUnless(NODE, "Node unavailable")
    def test_node_fixture_real_http_restart_and_cleanup(self):
        template = ROOT / "templates/testing/node/http_fixture.mjs.example"
        shutil.copyfile(template, self.root / "http_fixture.mjs")
        script = self.root / "fixture.test.mjs"
        script.write_text("""import test from 'node:test';
import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFile,writeFile,access} from 'node:fs/promises';
import {join} from 'node:path';
import {withTempDirectory,withHttpServer} from './http_fixture.mjs';
test('isolated HTTP persistence fixture', async()=>{
 let removed;
 await withTempDirectory(async(dir)=>{
  removed=dir;
  const factory=()=>createServer(async(req,res)=>{
   if(req.method==='POST'){
    const chunks=[];for await(const c of req)chunks.push(c);
    await writeFile(join(dir,'value.json'),Buffer.concat(chunks));res.writeHead(201);res.end();
   }else{res.end(await readFile(join(dir,'value.json')));}
  });
  await withHttpServer(factory,async(client)=>{
   assert.equal((await client.request('POST','/',{value:7})).status,201);
   await assert.rejects(()=>client.request('GET','https://example.invalid/'));
  });
  await withHttpServer(factory,async(client)=>assert.deepEqual((await client.request('GET','/')).json(),{value:7}));
 });
 await assert.rejects(()=>access(removed));
});
""")
        result = kit.record_check(self.root, "node-fixture", [NODE, "--test", "--test-reporter=tap", str(script)], 10)
        self.assertEqual(result["result"], "PASS", result["stdout"] + result["stderr"])
        self.assertEqual(result["tests"]["effective"], 1)

    def test_skeleton_cannot_be_mistaken_for_a_completed_feature_test(self):
        helpers = ROOT / "templates/testing/python"
        shutil.copyfile(helpers / "test_feature.py.example", self.root / "test_feature.py")
        import sys
        record = kit.record_check(self.root, "skeleton", [sys.executable, "-m", "unittest", "discover", "-v"], 10)
        self.assertEqual(record["result"], "NOT_RUN")

    @unittest.skipUnless(NODE, "Node unavailable")
    def test_node_reference_skeleton_is_not_run(self):
        source = ROOT / "templates/testing/node/feature.test.mjs.example"
        shutil.copyfile(source, self.root / "feature.test.mjs")
        record = kit.record_check(self.root, "node-skeleton", [NODE, "--test", "--test-reporter=tap"], 10)
        self.assertEqual(record["result"], "NOT_RUN")


if __name__ == "__main__":
    unittest.main()
