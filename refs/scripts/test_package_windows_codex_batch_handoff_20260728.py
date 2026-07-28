#!/usr/bin/env python3

import hashlib
import importlib.util
import io
import json
import stat
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "package_windows_codex_batch_handoff_20260728.py"
SPEC = importlib.util.spec_from_file_location("batch_packager_20260728", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


class BatchPackagerTests(unittest.TestCase):
    def child(
        self,
        root: Path,
        job_id: str,
        member: str = "run.ps1",
        entrypoint: str = "run.ps1",
    ) -> Path:
        directory = root / job_id
        directory.mkdir()
        package = directory / "package.zip"
        with zipfile.ZipFile(package, "w") as archive:
            archive.writestr(member, f"Write-Host {job_id}\n")
        sha = hashlib.sha256(package.read_bytes()).hexdigest()
        manifest = {
            "schema": "windows_codex_batch_job_v1",
            "job_id": job_id,
            "package": "package.zip",
            "package_sha256": sha,
            "entrypoint": entrypoint,
            "failure_policy": "independent",
        }
        path = directory / "job.json"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        return path

    def valid_return_members(
        self,
        request: Path,
        statuses: tuple[str, ...] = ("answered", "exact_bind_failure"),
    ) -> dict[str, bytes]:
        with zipfile.ZipFile(request) as archive:
            manifest_bytes = archive.read("BATCH_MANIFEST.json")
            contract_bytes = archive.read("BATCH_RETURN_CONTRACT.json")
        manifest = json.loads(manifest_bytes)
        contract = json.loads(contract_bytes)
        self.assertEqual(len(contract["expected_jobs"]), len(statuses))
        jobs = []
        members = {
            "BATCH_MANIFEST.json": manifest_bytes,
            "BATCH_RETURN_CONTRACT.json": contract_bytes,
        }
        for expected, status in zip(contract["expected_jobs"], statuses):
            evidence_path = expected["evidence_root"] + "evidence.txt"
            evidence_bytes = f"{expected['job_id']} {status}\n".encode()
            members[evidence_path] = evidence_bytes
            jobs.append({
                "order": expected["order"],
                "job_id": expected["job_id"],
                "request_package_sha256": expected["request_package_sha256"],
                "status": status,
                "evidence": [{
                    "path": evidence_path,
                    "sha256": hashlib.sha256(evidence_bytes).hexdigest(),
                    "kind": "diagnostic",
                    "description": "terminal job evidence",
                }],
                "failure": None if status == "answered" else {
                    "stage": "exact_binding",
                    "reason": "binding unavailable",
                },
            })
        parent_status = (
            "answered"
            if all(status == "answered" for status in statuses)
            else "exact_bind_failure"
            if all(status == "exact_bind_failure" for status in statuses)
            else "partial_success"
        )
        members["BATCH_RETURN.json"] = MODULE.canonical_json({
            "$schema": MODULE.RETURN_RECORD_SCHEMA,
            "batch_id": manifest["batch_id"],
            "request_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
            "request_return_contract_sha256": hashlib.sha256(contract_bytes).hexdigest(),
            "status": parent_status,
            "jobs": jobs,
        })
        return members

    def write_return(self, path: Path, members: dict[str, bytes]) -> None:
        payload = dict(members)
        payload.pop("CHECKSUMS.sha256", None)
        payload["CHECKSUMS.sha256"] = "".join(
            f"{hashlib.sha256(payload[name]).hexdigest()}  {name}\n"
            for name in sorted(payload)
        ).encode()
        MODULE.deterministic_zip(path, payload)

    def mutate_return_record(self, members: dict[str, bytes], mutate) -> None:
        record = json.loads(members["BATCH_RETURN.json"])
        mutate(record)
        members["BATCH_RETURN.json"] = MODULE.canonical_json(record)

    def test_builds_portable_deterministic_bound_batch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            one = self.child(root, "one")
            two = self.child(root, "two")
            first = root / "first.zip"
            second = root / "second.zip"
            result = MODULE.package("batch_1", [one, two], first)
            MODULE.package("batch_1", [one, two], second)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(result["output_zip_sha256"], hashlib.sha256(first.read_bytes()).hexdigest())
            with zipfile.ZipFile(first) as archive:
                names = archive.namelist()
                self.assertFalse(any("__MACOSX" in name for name in names))
                manifest = json.loads(archive.read("BATCH_MANIFEST.json"))
                self.assertEqual([j["order"] for j in manifest["jobs"]], [1, 2])
                self.assertEqual(manifest["start_gate"], "HOLD")
                self.assertEqual(manifest["$schema"], "windows_codex_batch_handoff_v2")
                self.assertEqual(
                    manifest["execution"]["required_jobs"],
                    "all_expected_jobs_exactly_once",
                )
                self.assertEqual(
                    manifest["execution"]["terminal_statuses"],
                    ["answered", "exact_bind_failure"],
                )
                self.assertEqual(manifest["execution"]["barrier"], "all_jobs_terminal")
                self.assertEqual(manifest["delivery"]["archive_count"], 1)
                self.assertEqual(manifest["delivery"]["mode"], "single_consolidated_zip")
                self.assertEqual(
                    manifest["delivery"]["emit_only_after"],
                    "all_jobs_terminal",
                )
                self.assertTrue(manifest["delivery"]["interim_delivery_forbidden"])
                self.assertTrue(
                    manifest["delivery"]["per_job_return_zip_delivery_forbidden"]
                )
                self.assertTrue(manifest["delivery"]["return_zip_members_forbidden"])
                instructions = archive.read("README_FIRST.md").decode()
                self.assertIn("Do not change Adobe preferences", instructions)
                self.assertIn("must not erase", instructions)
                self.assertIn("execute every expected job exactly once", instructions)
                self.assertIn("Every job must reach exactly one terminal status", instructions)
                self.assertIn("Do not emit, upload, attach, or return any interim result", instructions)
                self.assertIn("Every nested ZIP under `jobs/` is forbidden", instructions)
                self.assertIn("emit exactly one consolidated parent ZIP", instructions)
                self.assertIn("delivery and its timing are external", instructions)
                contract = json.loads(archive.read("BATCH_RETURN_CONTRACT.json"))
                self.assertEqual(contract["$schema"], "windows_codex_batch_return_v2")
                self.assertEqual(contract["expected_job_count"], 2)
                self.assertEqual(contract["completion"]["barrier"], "all_jobs_terminal")
                self.assertEqual(contract["delivery"], manifest["delivery"])
                self.assertEqual(
                    contract["evidence_requirements"]["minimum_entries_per_job"],
                    1,
                )
                self.assertEqual(
                    contract["evidence_requirements"]["required_fields"],
                    ["path", "sha256", "kind", "description"],
                )
                self.assertTrue(
                    contract["evidence_requirements"]["direct_regular_non_zip_files_only"]
                )
                self.assertTrue(contract["preserve_successful_jobs"])
                self.assertEqual(
                    contract["allowed_parent_statuses"],
                    ["answered", "partial_success", "exact_bind_failure"],
                )
                self.assertEqual(contract["status_rules"]["exact_bind_failure"], "zero child jobs answered")
                self.assertEqual(len(contract["expected_jobs"]), 2)
                self.assertNotIn("<", json.dumps(contract))
                self.assertEqual(
                    contract["return_record_keys"],
                    [
                        "$schema",
                        "batch_id",
                        "request_manifest_sha256",
                        "request_return_contract_sha256",
                        "status",
                        "jobs",
                    ],
                )
                for job in contract["expected_jobs"]:
                    self.assertNotIn("return_zip", job)
                    self.assertTrue(job["evidence_root"].startswith("jobs/"))
                self.assertEqual(
                    contract["allowlisted_return_members"]["unexpected_or_unreferenced_members"],
                    "forbidden",
                )
                self.assertEqual(
                    contract["evidence_requirements"]["path_scope"],
                    "exactly_one_nonempty_component_below_exact_ordered_job_directory",
                )
                self.assertEqual(
                    contract["allowlisted_return_members"][
                        "nested_zip_extension_magic_or_valid_payload_under_jobs"
                    ],
                    "forbidden",
                )
                self.assertEqual(
                    contract["delivery"]["session_policy_enforcement"],
                    "external_to_archive_intake",
                )
                intake = json.loads(archive.read("INTAKE_SCHEMA.json"))
                self.assertEqual(intake["$schema"], "windows_codex_batch_intake_v2")
                self.assertEqual(intake["expected_job_count"], 2)
                self.assertEqual(intake["completion"], contract["completion"])
                self.assertEqual(intake["delivery"], contract["delivery"])
                self.assertEqual(
                    intake["evidence_requirements"],
                    contract["evidence_requirements"],
                )
                self.assertEqual(
                    intake["request_bindings"]["batch_manifest_sha256"],
                    hashlib.sha256(archive.read("BATCH_MANIFEST.json")).hexdigest(),
                )
                self.assertEqual(
                    intake["request_bindings"]["batch_return_contract_sha256"],
                    hashlib.sha256(archive.read("BATCH_RETURN_CONTRACT.json")).hexdigest(),
                )
                validations = "\n".join(intake["validation"])
                self.assertIn("every expected job exactly once", validations)
                self.assertIn("at least one non-empty evidence entry", validations)
                self.assertIn(
                    "nested ZIP by .zip extension, ZIP magic, or valid ZIP payload",
                    validations,
                )
                self.assertIn("delivery count and timing remain an external session policy", validations)
                self.assertFalse(
                    any(Path(name).name.casefold() == "return.zip" for name in names)
                )
                checksum_lines = archive.read("CHECKSUMS.sha256").decode().splitlines()
                self.assertEqual(len(checksum_lines), len(names) - 1)

    def test_preflights_aliases_and_rejects_existing_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self.child(root, "one")
            package = manifest.parent / "package.zip"
            original_package = package.read_bytes()
            with self.assertRaisesRegex(MODULE.ContractError, "aliases an immutable input"):
                MODULE.package("batch_1", [manifest], package)
            self.assertEqual(package.read_bytes(), original_package)

            output = root / "existing.zip"
            output.write_bytes(b"unrelated")
            with self.assertRaisesRegex(MODULE.ContractError, "already exists"):
                MODULE.package("batch_1", [manifest], output)
            self.assertEqual(output.read_bytes(), b"unrelated")
            self.assertFalse((root / "existing.zip.sha256").exists())

            output = root / "sidecar_exists.zip"
            sidecar = root / "sidecar_exists.zip.sha256"
            sidecar.write_bytes(b"unrelated checksum")
            with self.assertRaisesRegex(MODULE.ContractError, "checksum sidecar already exists"):
                MODULE.package("batch_1", [manifest], output)
            self.assertFalse(output.exists())
            self.assertEqual(sidecar.read_bytes(), b"unrelated checksum")

    def test_snapshots_child_bytes_once_for_hash_size_and_embedding(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self.child(root, "one")
            package = manifest.parent / "package.zip"
            original_package = package.read_bytes()
            original_read_bytes = Path.read_bytes
            package_reads = 0

            def mutate_after_snapshot(path):
                nonlocal package_reads
                data = original_read_bytes(path)
                if path.resolve() == package.resolve():
                    package_reads += 1
                    if package_reads == 1:
                        package.write_bytes(b"mutated after snapshot")
                return data

            output = root / "snapshot.zip"
            with mock.patch.object(Path, "read_bytes", mutate_after_snapshot):
                MODULE.package("batch_1", [manifest], output)
            self.assertEqual(package_reads, 1)
            with zipfile.ZipFile(output) as archive:
                embedded = archive.read("jobs/001_one/package.zip")
                job_manifest = json.loads(archive.read("jobs/001_one/job_manifest.json"))
            self.assertEqual(embedded, original_package)
            self.assertEqual(job_manifest["package_size_bytes"], len(original_package))
            self.assertEqual(
                job_manifest["package_sha256"],
                hashlib.sha256(original_package).hexdigest(),
            )

    def test_atomic_failure_cleans_reserved_targets_and_temps(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self.child(root, "one")
            output = root / "atomic.zip"
            sidecar = root / "atomic.zip.sha256"
            original_replace = MODULE.os.replace
            calls = 0

            def fail_second_replace(source, destination):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("simulated sidecar install failure")
                return original_replace(source, destination)

            with mock.patch.object(MODULE.os, "replace", side_effect=fail_second_replace):
                with self.assertRaisesRegex(OSError, "simulated"):
                    MODULE.package("batch_1", [manifest], output)
            self.assertFalse(output.exists())
            self.assertFalse(sidecar.exists())
            self.assertEqual(list(root.glob(".atomic.zip.*.tmp")), [])
            self.assertEqual(list(root.glob(".atomic.zip.sha256.*.tmp")), [])

    def test_keyboard_interrupt_cleans_reserved_targets_and_temps(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self.child(root, "one")
            output = root / "interrupt.zip"
            sidecar = root / "interrupt.zip.sha256"
            with mock.patch.object(MODULE.os, "replace", side_effect=KeyboardInterrupt):
                with self.assertRaises(KeyboardInterrupt):
                    MODULE.package("batch_1", [manifest], output)
            self.assertFalse(output.exists())
            self.assertFalse(sidecar.exists())
            self.assertEqual(list(root.glob(".interrupt.zip.*.tmp")), [])
            self.assertEqual(list(root.glob(".interrupt.zip.sha256.*.tmp")), [])

    def test_validates_complete_consolidated_return(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            request = root / "request.zip"
            MODULE.package(
                "batch_1",
                [self.child(root, "one"), self.child(root, "two")],
                request,
            )
            returned = root / "returned.zip"
            self.write_return(returned, self.valid_return_members(request))
            result = MODULE.validate_return_archive(request, returned)
            self.assertEqual(result["status"], "partial_success")
            self.assertEqual(result["job_count"], 2)

    def test_validate_return_cli_accepts_valid_and_rejects_invalid(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            request = root / "request.zip"
            MODULE.package(
                "batch_1",
                [self.child(root, "one"), self.child(root, "two")],
                request,
            )
            returned = root / "returned.zip"
            self.write_return(returned, self.valid_return_members(request))
            valid = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--validate-return",
                    str(request),
                    str(returned),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(valid.returncode, 0, valid.stderr)
            self.assertEqual(json.loads(valid.stdout)["status"], "partial_success")

            invalid = root / "invalid.zip"
            invalid.write_bytes(b"not a ZIP")
            rejected = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--validate-return",
                    str(request),
                    str(invalid),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("not a valid ZIP", rejected.stderr)

    def test_rejects_adversarial_return_archives(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            request = root / "request.zip"
            MODULE.package(
                "batch_1",
                [self.child(root, "one"), self.child(root, "two")],
                request,
            )

            cases = []

            def renamed_zip_magic(members):
                record = json.loads(members["BATCH_RETURN.json"])
                path = record["jobs"][0]["evidence"][0]["path"]
                members[path] = b"PK\x03\x04renamed zip payload"
                record["jobs"][0]["evidence"][0]["sha256"] = hashlib.sha256(members[path]).hexdigest()
                members["BATCH_RETURN.json"] = MODULE.canonical_json(record)

            cases.append(("renamed_zip_magic", renamed_zip_magic, "nested ZIP archive/payload"))

            def sfx_zip_payload(members):
                archive_bytes = io.BytesIO()
                with zipfile.ZipFile(archive_bytes, "w") as nested:
                    nested.writestr("payload.txt", "nested")
                record = json.loads(members["BATCH_RETURN.json"])
                path = record["jobs"][0]["evidence"][0]["path"]
                members[path] = b"MZ-self-extracting-preamble" + archive_bytes.getvalue()
                record["jobs"][0]["evidence"][0]["sha256"] = hashlib.sha256(members[path]).hexdigest()
                members["BATCH_RETURN.json"] = MODULE.canonical_json(record)

            cases.append(("sfx_zip_payload", sfx_zip_payload, "nested ZIP archive/payload"))

            def nested_zip_extension(members):
                record = json.loads(members["BATCH_RETURN.json"])
                old_path = record["jobs"][0]["evidence"][0]["path"]
                new_path = old_path.removesuffix(".txt") + ".zip"
                members[new_path] = members.pop(old_path)
                record["jobs"][0]["evidence"][0]["path"] = new_path
                members["BATCH_RETURN.json"] = MODULE.canonical_json(record)

            cases.append(("nested_zip_extension", nested_zip_extension, "nested ZIP archive/payload"))

            def nested_evidence_path(members):
                record = json.loads(members["BATCH_RETURN.json"])
                old_path = record["jobs"][0]["evidence"][0]["path"]
                prefix, filename = old_path.rsplit("/", 1)
                new_path = f"{prefix}/nested/{filename}"
                members[new_path] = members.pop(old_path)
                record["jobs"][0]["evidence"][0]["path"] = new_path
                members["BATCH_RETURN.json"] = MODULE.canonical_json(record)

            cases.append((
                "nested_evidence_path",
                nested_evidence_path,
                "exactly one direct path component",
            ))

            cases.append((
                "altered_child_sha",
                lambda members: self.mutate_return_record(
                    members,
                    lambda record: record["jobs"][0].__setitem__(
                        "request_package_sha256",
                        "0" * 64,
                    ),
                ),
                "identity/order/request SHA mismatch",
            ))
            for value, label in ((True, "boolean_order"), (1.0, "float_order")):
                cases.append((
                    label,
                    lambda members, value=value: self.mutate_return_record(
                        members,
                        lambda record, value=value: record["jobs"][0].__setitem__(
                            "order",
                            value,
                        ),
                    ),
                    "order must be a strict integer",
                ))
            cases.append((
                "wrong_parent_aggregation",
                lambda members: self.mutate_return_record(
                    members,
                    lambda record: record.__setitem__("status", "answered"),
                ),
                "parent status aggregation mismatch",
            ))
            cases.append((
                "missing_failure",
                lambda members: self.mutate_return_record(
                    members,
                    lambda record: record["jobs"][1].__setitem__("failure", None),
                ),
                "requires failure",
            ))
            cases.append((
                "missing_evidence",
                lambda members: self.mutate_return_record(
                    members,
                    lambda record: record["jobs"][0].__setitem__("evidence", []),
                ),
                "requires at least one evidence entry",
            ))
            cases.append((
                "extra_file",
                lambda members: members.__setitem__("jobs/001_one/unreferenced.txt", b"extra"),
                "unexpected or unreferenced members",
            ))
            cases.append((
                "altered_manifest_copy",
                lambda members: members.__setitem__(
                    "BATCH_MANIFEST.json",
                    members["BATCH_MANIFEST.json"] + b" ",
                ),
                "not the immutable request copy",
            ))

            for index, (name, mutate, reason) in enumerate(cases):
                with self.subTest(name=name):
                    members = self.valid_return_members(request)
                    mutate(members)
                    returned = root / f"adversarial_{index}.zip"
                    self.write_return(returned, members)
                    with self.assertRaisesRegex(MODULE.ContractError, reason):
                        MODULE.validate_return_archive(request, returned)

    def test_rejects_duplicate_ids_and_duplicate_sha(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = self.child(root, "first")
            duplicate_id_dir = root / "other"
            duplicate_id_dir.mkdir()
            package = duplicate_id_dir / "package.zip"
            package.write_bytes((first.parent / "package.zip").read_bytes())
            sha = hashlib.sha256(package.read_bytes()).hexdigest()
            duplicate = duplicate_id_dir / "job.json"
            duplicate.write_text(json.dumps({
                "schema": "windows_codex_batch_job_v1", "job_id": "first",
                "package": "package.zip", "package_sha256": sha,
                "entrypoint": "run.ps1", "failure_policy": "independent",
            }), encoding="utf-8")
            with self.assertRaisesRegex(MODULE.ContractError, "duplicate job_id"):
                MODULE.package("batch_1", [first, duplicate], root / "out.zip")
            duplicate.write_text(duplicate.read_text().replace('"first"', '"second"', 1), encoding="utf-8")
            with self.assertRaisesRegex(MODULE.ContractError, "duplicate child package SHA"):
                MODULE.package("batch_1", [first, duplicate], root / "out.zip")

    def test_rejects_sha_drift_missing_checksum_and_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self.child(root, "job")
            body = json.loads(manifest.read_text())
            body["package_sha256"] = "0" * 64
            manifest.write_text(json.dumps(body), encoding="utf-8")
            with self.assertRaisesRegex(MODULE.ContractError, "SHA-256 drift"):
                MODULE.package("batch_1", [manifest], root / "out.zip")
            del body["package_sha256"]
            manifest.write_text(json.dumps(body), encoding="utf-8")
            with self.assertRaisesRegex(MODULE.ContractError, "missing or invalid"):
                MODULE.package("batch_1", [manifest], root / "out.zip")
            body["package_sha256"] = "0" * 64
            body["package"] = "../package.zip"
            manifest.write_text(json.dumps(body), encoding="utf-8")
            with self.assertRaisesRegex(MODULE.ContractError, "unsafe"):
                MODULE.package("batch_1", [manifest], root / "out.zip")

    def test_rejects_unsafe_child_member_and_macosx(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for job_id, member in (("escape", "../x"), ("mac", "__MACOSX/._x")):
                manifest = self.child(root, job_id, member)
                with self.assertRaises(MODULE.ContractError):
                    MODULE.package("batch_1", [manifest], root / f"{job_id}.zip")

    def test_entrypoint_must_be_exact_regular_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self.child(root, "caseonly", "Run.ps1")
            with self.assertRaisesRegex(MODULE.ContractError, "exact regular-file"):
                MODULE.package("batch_1", [manifest], root / "caseonly.zip")
            manifest = self.child(root, "directory", "run.ps1/")
            with self.assertRaisesRegex(MODULE.ContractError, "exact regular-file"):
                MODULE.package("batch_1", [manifest], root / "directory.zip")

    def test_rejects_windows_invalid_members(self):
        adversarial = (
            ("device", "CON.txt", "reserved DOS device"),
            ("device_ext", "dir/lpt1.log", "reserved DOS device"),
            ("com_sup_1", "COM¹.txt", "reserved DOS device"),
            ("com_sup_2", "com²", "reserved DOS device"),
            ("com_sup_3", "Com³.log", "reserved DOS device"),
            ("lpt_sup_1", "LPT¹.txt", "reserved DOS device"),
            ("lpt_sup_2", "lpt²", "reserved DOS device"),
            ("lpt_sup_3", "Lpt³.log", "reserved DOS device"),
            ("ads", "run.ps1:stream", "colon/ADS"),
            ("question", "run?.ps1", "Windows-forbidden character/control"),
            ("trailing_dot", "dir./run.ps1", "trailing dot/space"),
            ("trailing_space", "dir /run.ps1", "trailing dot/space"),
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for job_id, member, reason in adversarial:
                manifest = self.child(root, job_id, member)
                with self.assertRaisesRegex(MODULE.ContractError, reason):
                    MODULE.package("batch_1", [manifest], root / f"{job_id}.zip")

    def test_windows_component_utf16_limit_accepts_255_rejects_256(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            accepted_name = "a" * 255
            accepted = self.child(
                root,
                "accepted255",
                member=accepted_name,
                entrypoint=accepted_name,
            )
            MODULE.package("batch_1", [accepted], root / "accepted.zip")

            rejected_name = "b" * 256
            rejected = self.child(
                root,
                "rejected256",
                member=rejected_name,
                entrypoint=rejected_name,
            )
            with self.assertRaisesRegex(MODULE.ContractError, "exceeds 255 UTF-16 code units"):
                MODULE.package("batch_1", [rejected], root / "rejected.zip")

    def test_rejects_job_id_with_trailing_dot(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self.child(root, "job.")
            with self.assertRaisesRegex(MODULE.ContractError, "invalid job_id"):
                MODULE.package("batch_1", [manifest], root / "out.zip")

    def test_rejects_casefold_and_hierarchy_collisions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for job_id, members, reason in (
                ("casefold", ("Run.ps1", "run.ps1"), "duplicate Windows member"),
                ("hierarchy", ("payload", "payload/run.ps1"), "hierarchy collision"),
            ):
                directory = root / job_id
                directory.mkdir()
                package = directory / "package.zip"
                with zipfile.ZipFile(package, "w") as archive:
                    for member in members:
                        archive.writestr(member, "x")
                manifest = directory / "job.json"
                manifest.write_text(json.dumps({
                    "schema": "windows_codex_batch_job_v1",
                    "job_id": job_id,
                    "package": "package.zip",
                    "package_sha256": hashlib.sha256(package.read_bytes()).hexdigest(),
                    "entrypoint": members[-1],
                    "failure_policy": "independent",
                }), encoding="utf-8")
                with self.assertRaisesRegex(MODULE.ContractError, reason):
                    MODULE.package("batch_1", [manifest], root / f"{job_id}.zip")

    def test_rejects_nonregular_unix_types_and_noncanonical_aliases(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cases = (
                ("fifo", "run.ps1", stat.S_IFIFO | 0o644, "invalid Unix member type"),
                ("dir_mode_no_slash", "run.ps1", stat.S_IFDIR | 0o755, "invalid Unix member type"),
                ("double_slash", "dir//run.ps1", stat.S_IFREG | 0o644, "not canonically spelled"),
            )
            for job_id, member, mode, reason in cases:
                directory = root / job_id
                directory.mkdir()
                package = directory / "package.zip"
                info = zipfile.ZipInfo(member)
                info.create_system = 3
                info.external_attr = mode << 16
                with zipfile.ZipFile(package, "w") as archive:
                    archive.writestr(info, "x")
                manifest = directory / "job.json"
                manifest.write_text(json.dumps({
                    "schema": "windows_codex_batch_job_v1",
                    "job_id": job_id,
                    "package": "package.zip",
                    "package_sha256": hashlib.sha256(package.read_bytes()).hexdigest(),
                    "entrypoint": "run.ps1",
                    "failure_policy": "independent",
                }), encoding="utf-8")
                with self.assertRaisesRegex(MODULE.ContractError, reason):
                    MODULE.package("batch_1", [manifest], root / f"{job_id}.zip")


if __name__ == "__main__":
    unittest.main()
