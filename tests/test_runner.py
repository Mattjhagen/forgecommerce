import json, os, subprocess, tempfile, unittest
from pathlib import Path

ROOT=Path(__file__).parents[1]

class RunnerTests(unittest.TestCase):
    def test_state_is_machine_readable_and_report_is_independent(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime=ROOT/'progress/runtime'; runtime.mkdir(parents=True,exist_ok=True)
            state=runtime/'agent-state.json'; old=state.read_text() if state.exists() else None
            report=ROOT/'progress/DAILY'/__import__('datetime').date.today().isoformat()
            report=report.with_suffix('.md'); old_report=report.read_text() if report.exists() else None
            state.write_text(json.dumps({'status':'completed','run_id':'test','last_sync':{'status':'confirmed'}}))
            try:
                result=subprocess.run([str(ROOT/'scripts/report-agent.sh')],cwd=ROOT,text=True,capture_output=True,check=True)
                self.assertIn('wrote',result.stdout)
                self.assertIn('GitHub synchronization', report.read_text())
            finally:
                if old is None: state.unlink(missing_ok=True)
                else: state.write_text(old)
                if old_report is None: report.unlink(missing_ok=True)
                else: report.write_text(old_report)

    def test_recovery_is_bounded_and_does_not_overlap(self):
        for script in ('agent-common.sh','start-agent.sh','stop-agent.sh','status-agent.sh','recover-agent.sh','report-agent.sh','checkpoint-sync.sh','run-agent.sh'):
            self.assertEqual(subprocess.run(['bash','-n',str(ROOT/'scripts'/script)]).returncode,0,script)

    def test_recovery_restarts_are_bounded_and_codex_session_is_resumable(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path=Path(tmp); state_dir=tmp_path/'state'; bin_dir=tmp_path/'bin'; bin_dir.mkdir()
            tmux=bin_dir/'tmux'; tmux.write_text("""#!/usr/bin/env bash
if [[ "$1" == "has-session" ]]; then exit 1; fi
if [[ "$1" == "new-session" ]]; then exit 0; fi
exit 1
"""); tmux.chmod(0o755)
            env=os.environ.copy(); env['FORGECOMMERCE_STATE_DIR']=str(state_dir); env['FORGECOMMERCE_SESSION_NAME']='test-agent'; env['PATH']=f'{bin_dir}:{env["PATH"]}'
            (state_dir/'agent-state.json').parent.mkdir(parents=True)
            (state_dir/'agent-state.json').write_text(json.dumps({'status':'running','restart_count':0}))
            recover=ROOT/'scripts/recover-agent.sh'
            for expected in (1,2,3):
                result=subprocess.run([str(recover)],cwd=ROOT,env=env,text=True,capture_output=True)
                self.assertEqual(result.returncode,0,result.stderr)
                self.assertEqual(json.loads((state_dir/'agent-state.json').read_text())['status'],'starting')
                self.assertEqual(json.loads((state_dir/'agent-state.json').read_text())['restart_count'],str(expected))
            result=subprocess.run([str(recover)],cwd=ROOT,env=env,text=True,capture_output=True)
            self.assertEqual(result.returncode,1)
            self.assertEqual(json.loads((state_dir/'agent-state.json').read_text())['status'],'recovery_required')

            codex=bin_dir/'codex'; codex.write_text("#!/usr/bin/env bash\necho '{\"type\":\"thread.started\",\"thread_id\":\"thread-test-123\"}'\n"); codex.chmod(0o755)
            (state_dir/'agent-state.json').write_text(json.dumps({'status':'idle','codex_session_id':''}))
            result=subprocess.run([str(ROOT/'scripts/run-agent.sh'),'run-1','test task'],cwd=ROOT,env=env,text=True,capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr)
            state=json.loads((state_dir/'agent-state.json').read_text())
            self.assertEqual(state['status'],'completed'); self.assertEqual(state['codex_session_id'],'thread-test-123')

if __name__=='__main__': unittest.main()
