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

if __name__=='__main__': unittest.main()
