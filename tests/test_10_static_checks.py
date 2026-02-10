from __future__ import annotations

from helpers import run_cmd



def test_py_compile_and_pyright(repo_root) -> None:
    compile_cmd = [
        "uv",
        "run",
        "python",
        "-m",
        "py_compile",
        "main.py",
        "generate_full_plan.py",
        "config.py",
        "novel_engine/core/ai_writer.py",
        "novel_engine/core/being_engine.py",
        "novel_engine/core/contracts.py",
        "novel_engine/core/view_models.py",
        "novel_engine/core/presenters.py",
        "novel_engine/core/person.py",
        "novel_engine/core/plan_builder.py",
        "novel_engine/data/database.py",
        "novel_engine/data/quiz_data.py",
    ]
    compile_res = run_cmd(compile_cmd, cwd=repo_root, timeout=60)
    assert compile_res.returncode == 0, (
        "STATIC_CHECK_FAILED(py_compile)\n"
        f"cmd={' '.join(compile_cmd)}\n"
        f"stdout={compile_res.stdout}\n"
        f"stderr={compile_res.stderr}"
    )

    pyright_cmd = ["uv", "run", "pyright", "novel_engine/core", "novel_engine/data"]
    pyright_res = run_cmd(pyright_cmd, cwd=repo_root, timeout=120)
    assert pyright_res.returncode == 0, (
        "STATIC_CHECK_FAILED(pyright)\n"
        f"cmd={' '.join(pyright_cmd)}\n"
        f"stdout={pyright_res.stdout}\n"
        f"stderr={pyright_res.stderr}"
    )
