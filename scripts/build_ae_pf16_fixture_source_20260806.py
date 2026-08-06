#!/usr/bin/env python3
"""Build the bounded PF16 fixture-source effect without installing it."""
from __future__ import annotations
import argparse, hashlib, json, shutil, subprocess, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; SOURCE=ROOT/"tools/ae_pf16_fixture_source"; PROJECT=ROOT/"aex_mac/ColorKeep/Mac/Skeleton.xcodeproj"
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument("--output",type=Path,default=ROOT/"tmp/ae_pf16_fixture_source_build");a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(prefix="olm_pf16_fixture_build_") as raw:
  stage=Path(raw); base=stage/"tools/ae_pf16_fixture_source"; mac=base/"Mac";mac.mkdir(parents=True)
  for name in ("Skeleton.cpp","Skeleton.h","Skeleton_Strings.cpp","Skeleton_Strings.h","SkeletonPiPL.r"): shutil.copy2(SOURCE/name,base/name)
  shutil.copy2(SOURCE/"Skeleton.plugin-Info.plist",mac/"Skeleton.plugin-Info.plist");shutil.copytree(PROJECT,mac/"Skeleton.xcodeproj")
  for name in ("Headers","Util","Resources"): (stage/name).symlink_to(ROOT/name)
  subprocess.run(["xcodebuild","-project",str(mac/"Skeleton.xcodeproj"),"-configuration","Debug","ARCHS=arm64 x86_64","ONLY_ACTIVE_ARCH=NO","CODE_SIGNING_ALLOWED=NO","MACOSX_DEPLOYMENT_TARGET=11.0","PRODUCT_NAME=OLMPF16FixtureSource","PRODUCT_BUNDLE_IDENTIFIER=com.olm.test.PF16FixtureSource","build"],check=True)
  found=list((stage/"tools/ae_pf16_fixture_source/Mac/build").rglob("OLMPF16FixtureSource.plugin"))
  if len(found)!=1: raise RuntimeError(f"product cardinality {found}")
  dest=a.output/"OLMPF16FixtureSource.plugin";shutil.rmtree(dest,ignore_errors=True);shutil.copytree(found[0],dest);subprocess.run(["codesign","--force","--sign","-",str(dest)],check=True)
  binary=dest/"Contents/MacOS/OLMPF16FixtureSource"; report={"status":"built_not_installed","bundle":str(dest),"binary_sha256":sha(binary),"architectures":subprocess.run(["lipo","-archs",str(binary)],check=True,capture_output=True,text=True).stdout.split(),"source_sha256":sha(SOURCE/"Skeleton.cpp")};print(json.dumps(report,indent=2));return 0
if __name__=="__main__": raise SystemExit(main())
