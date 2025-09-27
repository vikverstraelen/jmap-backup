from click.testing import CliRunner
from jmap_backup.cli import cli
from jmap_backup.tiny_jmap import TinyJMAPClient

def test_version():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert result.output.startswith("cli, version ")

def test_tiny_jmap_client_init():
    client = TinyJMAPClient("example.com", "user", "token")
    assert client.hostname == "example.com"
    assert client.username == "user"
    assert client.token == "token"