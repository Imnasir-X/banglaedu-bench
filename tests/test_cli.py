from banglaedu_bench.cli import main


def test_validate_dev():
    assert main(["validate", "dev"]) == 0


def test_stats(capsys):
    assert main(["stats", "dev"]) == 0
    assert '"mcq"' in capsys.readouterr().out


def test_run_and_leaderboard(tmp_path, capsys):
    assert main(["run", "--model", "mock-oracle", "--split", "dev", "--out", str(tmp_path)]) == 0
    assert main(["leaderboard", "--results", str(tmp_path), "--out", str(tmp_path / "lb")]) == 0
    assert (tmp_path / "lb" / "leaderboard_dev.md").exists()


def test_commit(tmp_path):
    out = tmp_path / "c.txt"
    assert main(["commit", "dev", "--out", str(out)]) == 0
    assert out.read_text().count("sha256:") > 0
