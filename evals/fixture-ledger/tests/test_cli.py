from ledger.cli import main


def test_missing_file_exits_2(tmp_path, capsys):
    assert main([str(tmp_path / "nope.csv")]) == 2
    assert "no such file" in capsys.readouterr().err
