import argparse
import os
import time
import subprocess
import sys
import glob
import shutil
import uuid


def newest_file_in(dirpath, since_ts):
    """outdir에서 가장 최근 생성된 파일 경로를 반환"""
    cand = []
    for p in glob.glob(os.path.join(dirpath, "*")):
        try:
            if os.path.isfile(p):
                mtime = os.path.getmtime(p)
                if mtime >= since_ts:
                    cand.append((mtime, p))
        except Exception:
            pass
    if not cand:
        return None
    cand.sort(key=lambda x: x[0], reverse=True)
    return cand[0][1]


def main():
    ap = argparse.ArgumentParser(description="FreeVC single-shot CLI wrapper (for original convert_cpu.py with --txtpath mode)")
    ap.add_argument("--hpfile", required=True, help="Path to FreeVC hyperparameter json file (e.g., ./configs/freevc-s.json)")
    ap.add_argument("--ptfile", required=True, help="Path to pretrained model (.pth)")
    ap.add_argument("--src_audio", required=True, help="Path to source/content audio")
    ap.add_argument("--ref_audio", required=True, help="Path to reference/speaker audio")
    ap.add_argument("--outdir", default="./outputs", help="Directory to save output files")
    ap.add_argument("--out", required=True, help="Final output wav path")
    ap.add_argument("--python_bin", default="/content/venv/bin/python", help="Python binary path to run convert_cpu.py")
    ap.add_argument("--use_timestamp", action="store_true", help="Append timestamp to the output filename (optional)")
    ap.add_argument("--extra", nargs=argparse.REMAINDER, default=[], help="Extra args passed to convert_cpu.py if needed")
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    # ✅ convert_cpu.py는 --txtpath 기반으로 작동하므로 임시 리스트 파일 생성
    tmp_list = f"/tmp/freevc_{uuid.uuid4().hex}.txt"
    title = os.path.splitext(os.path.basename(args.out))[0]
    with open(tmp_list, "w") as f:
        # title|src|ref 형식으로 작성
        f.write(f"{title}|{os.path.abspath(args.src_audio)}|{os.path.abspath(args.ref_audio)}\n")

    # ✅ convert_cpu.py 실행 커맨드 (txtpath 방식)
    cmd = [
        args.python_bin, "convert_cpu.py",
        "--hpfile", args.hpfile,
        "--ptfile", args.ptfile,
        "--txtpath", tmp_list,
        "--outdir", args.outdir
    ]
    if args.use_timestamp:
        cmd.append("--use_timestamp")
    if args.extra:
        cmd += args.extra

    # 실행 로그
    print("[FreeVC] Running:", " ".join(cmd), flush=True)
    start_ts = time.time()

    # ✅ subprocess로 FreeVC 변환 수행
    rc = subprocess.call(cmd)
    if rc != 0:
        print(f"[FreeVC] convert_cpu.py failed with code {rc}", file=sys.stderr)
        sys.exit(rc)

    # ✅ outputs 폴더에서 변환된 최신 파일 탐색
    newest = newest_file_in(args.outdir, since_ts=start_ts)
    if newest is None:
        print("[FreeVC] No output file found in outdir.", file=sys.stderr)
        sys.exit(2)

    # ✅ 최종 결과 파일을 지정한 이름으로 복사
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    if os.path.abspath(newest) != os.path.abspath(args.out):
        shutil.copy2(newest, args.out)

    print(f"[FreeVC] Done. Output saved -> {args.out}")

    # ✅ 임시 txt파일 삭제
    try:
        os.remove(tmp_list)
    except Exception:
        pass


if __name__ == "__main__":
    main()
